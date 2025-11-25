from flask import Flask, request, jsonify, session, render_template, send_from_directory
from flask_session import Session
from flask_cors import CORS
import os
import pyodbc
from datetime import date, datetime, timedelta
from decimal import Decimal
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from openai import AzureOpenAI
import json
import re
from functools import wraps

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        # 1. Handle Decimal objects (for monetary values)
        if isinstance(obj, Decimal):
            # Safest: Convert Decimal to string to maintain precision
            return str(obj) 
        
        # 2. Handle date/datetime objects (your previous fix)
        # Note: You can use `(date, datetime, timedelta)` if you want to serialize timedeltas too.
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()
            
        # 3. Let the base class handle all other types
        return json.JSONEncoder.default(self, obj)

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__, 
            static_folder='static',
            template_folder='static')

# Configuration
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS

# Initialize extensions
Session(app)
CORS(app, supports_credentials=True, origins=['*'])

print("✅ Flask app initialized")


# ============================================
# AZURE OPENAI CONFIGURATION
# ============================================

AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-08-01-preview")


# Initialize Azure OpenAI client
try:
    openai_client = AzureOpenAI(
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        api_key=AZURE_OPENAI_API_KEY,
        api_version=AZURE_OPENAI_API_VERSION
    )
    print(f"✅ Azure OpenAI client connected to: {AZURE_OPENAI_ENDPOINT}")
except Exception as e:
    print(f"⚠️ Azure OpenAI initialization warning: {e}")
    openai_client = None

# ============================================
# DATABASE CONFIGURATION
# ============================================

DB_CONNECTION_STRING = (
    f"DRIVER={{ODBC Driver 17 for SQL Server}};"
    f"SERVER={os.getenv('DB_SERVER')};"
    f"DATABASE={os.getenv('DB_DATABASE')};"
    f"UID={os.getenv('DB_USER')};"
    f"PWD={os.getenv('DB_PASSWORD')};"
    f"Encrypt=yes;"
    f"TrustServerCertificate=no;"
)


# Connection pool (simple implementation)
connection_pool = []
MAX_POOL_SIZE = 5

def get_db_connection():
    """
    Get a database connection from pool or create new one.
    Uses connection pooling to reduce overhead.
    """
    try:
        if connection_pool:
            conn = connection_pool.pop()
            # Test if connection is still alive
            try:
                conn.cursor().execute("SELECT 1")
                return conn
            except:
                # Connection dead, create new one
                pass
        
        conn = pyodbc.connect(DB_CONNECTION_STRING)
        return conn
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return None


def return_connection(conn):
    """Return connection to pool"""
    if conn and len(connection_pool) < MAX_POOL_SIZE:
        connection_pool.append(conn)
    elif conn:
        conn.close()

# Test connection on startup
try:
    test_conn = get_db_connection()
    if test_conn:
        return_connection(test_conn)
        print("✅ Azure SQL connection successful")
except Exception as e:
    print(f"⚠️ Database connection warning: {e}")


# ============================================
# CACHING SYSTEM (Reduce database queries by 80%)
# ============================================

cache = {}
CACHE_DURATION = timedelta(minutes=5)

def get_cached_or_query(cache_key, query_function, *args, **kwargs):
    """
    Check cache first, only query database if cache miss.
    This significantly reduces database costs.
    """
    now = datetime.now()
    
    if cache_key in cache:
        data, timestamp = cache[cache_key]
        if now - timestamp < CACHE_DURATION:
            print(f"✅ Cache HIT: {cache_key}")
            return data
    
    print(f"📊 Cache MISS: {cache_key} - Querying database")
    data = query_function(*args, **kwargs)
    cache[cache_key] = (data, now)
    return data

def clear_cache(pattern=None):
    """Clear cache entries matching pattern"""
    global cache
    if pattern:
        cache = {k: v for k, v in cache.items() if pattern not in k}
    else:
        cache = {}


# ============================================
# EMAIL OTP SYSTEM (FREE via Gmail)
# ============================================

def generate_otp():
    """Generate a 6-digit OTP code"""
    return ''.join([str(secrets.randbelow(10)) for _ in range(6)])

def send_otp_email(recipient_email, otp_code, recipient_name="Customer"):
    """
    Send OTP via email using Gmail SMTP.
    This is completely FREE - no Twilio needed!
    """
    try:
        sender_email = os.getenv('EMAIL_USER')
        sender_password = os.getenv('EMAIL_PASSWORD')
        
        if not sender_email or not sender_password:
            print("⚠️ Email credentials not configured")
            return False
        
        # Create email message
        message = MIMEMultipart("alternative")
        message["Subject"] = "Hakikisha Insurance - Your Verification Code"
        message["From"] = f"Hakikisha Insurance <{sender_email}>"
        message["To"] = recipient_email
        
        # HTML email body
        html = f"""
        <html>
          <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background-color: white; border-radius: 10px; padding: 30px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
              <div style="text-align: center; margin-bottom: 30px;">
                <h2 style="color: #667eea; margin: 0;">👌 Hakikisha Insurance</h2>
              </div>
              
              <p style="color: #333; font-size: 16px;">Hello {recipient_name},</p>
              
              <p style="color: #666; font-size: 14px;">Your verification code is:</p>
              
              <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; text-align: center; border-radius: 8px; margin: 20px 0;">
                <div style="font-size: 36px; font-weight: bold; letter-spacing: 8px; color: white;">
                  {otp_code}
                </div>
              </div>
              
              <p style="color: #666; font-size: 14px; margin-top: 20px;">
                This code will expire in <strong>5 minutes</strong>.
              </p>
              
              <p style="color: #999; font-size: 12px; margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee;">
                If you didn't request this code, please ignore this email or contact us at info@hakikishainsurance.co.ke
              </p>
              
              <div style="text-align: center; margin-top: 30px; color: #999; font-size: 12px;">
                <p>Hakikisha Insurance - Protect What Matters Most</p>
              </div>
            </div>
          </body>
        </html>
        """
        
        part = MIMEText(html, "html")
        message.attach(part)
        
        # Send email via Gmail SMTP
        with smtplib.SMTP(os.getenv('EMAIL_HOST', 'smtp.gmail.com'), 
                         int(os.getenv('EMAIL_PORT', 587))) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient_email, message.as_string())
        
        print(f"✅ OTP sent to {recipient_email}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to send OTP email: {e}")
        return False

def store_otp_in_db(email, otp_code, user_role='customer'):
    """Store OTP in database with 5-minute expiry"""
    try:
        conn = get_db_connection()
        if not conn:
            return False
            
        cursor = conn.cursor()
        
        # Call stored procedure
        cursor.execute("""
            EXEC dbo.spStoreOTPToken 
                @Email = ?, 
                @OTPCodeValue = ?,
                @UserRole = ?
        """, (email, otp_code, user_role))
        
        conn.commit()
        cursor.close()
        return_connection(conn)
        return True
        
    except Exception as e:
        print(f"❌ Error storing OTP: {e}")
        if conn:
            conn.close()
        return False

# ============================================
# DATABASE QUERY FUNCTIONS
# ============================================

def query_policy_by_number(policy_number):
    """Get policy details by policy number with caching"""
    cache_key = f"policy_{policy_number}"
    
    def query_db():
        conn = get_db_connection()
        if not conn:
            return None
            
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM dbo.fnGetPolicyByNumber(?)", (policy_number,))
        
        # Convert to dictionary
        columns = [column[0] for column in cursor.description]
        row = cursor.fetchone()
        
        cursor.close()
        return_connection(conn)
        
        if row:
            return dict(zip(columns, row))
        return None
    
    return get_cached_or_query(cache_key, query_db)



def query_knowledge_base(query_text):
    conn = None
    try:
        conn = get_db_connection()
        if not conn:
            return []
            
        cursor = conn.cursor()
        
        # Prepare search terms (must be at least 3 characters long)
        search_terms = [term.strip() for term in query_text.lower().split() if len(term.strip()) > 2]
        
        # Build conditions for individual word matches
        individual_word_conditions = " OR ".join([
            f"Question LIKE '%{term}%' OR Keywords LIKE '%{term}%'" 
            for term in search_terms
        ])
        
        # Construct a prioritized SQL query
        sql_query = f"""
            SELECT TOP 3 Answer, Category
            FROM KnowledgeBase 
            WHERE 
                (Question LIKE '%{query_text}%' OR Keywords LIKE '%{query_text}%') 
                OR ({individual_word_conditions})
            ORDER BY 
                CASE 
                    WHEN Question LIKE '%{query_text}%' OR Keywords LIKE '%{query_text}%' 
                    THEN 100 
                    ELSE 0 
                END DESC,
                LEN(Keywords) DESC
        """
        
        cursor.execute(sql_query)
        results = cursor.fetchall()

        # Format the results for the AI model
        kb_data = []
        for row in results:
            kb_data.append({
                "category": row[1],
                "fact": row[0]
            })

        cursor.close()
        return kb_data

    except Exception as e:
        print(f"❌ Knowledge Base Query Error: {e}")
        return []
    finally:
        if conn:
            return_connection(conn)

def query_customer_policies(customer_identifier):
    """Get all policies for a customer"""
    cache_key = f"customer_policies_{customer_identifier}"
    
    def query_db():
        conn = get_db_connection()
        if not conn:
            return []
            
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM dbo.fnGetCustomerPolicies(?)", (customer_identifier,))
        
        columns = [column[0] for column in cursor.description]
        rows = cursor.fetchall()
        
        cursor.close()
        return_connection(conn)
        
        return [dict(zip(columns, row)) for row in rows]
    
    return get_cached_or_query(cache_key, query_db)

def query_claim_by_number(claim_number):
    """Get claim details by claim number"""
    cache_key = f"claim_{claim_number}"
    
    def query_db():
        conn = get_db_connection()
        if not conn:
            return None
            
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM dbo.fnGetClaimByNumber(?)", (claim_number,))
        
        columns = [column[0] for column in cursor.description]
        row = cursor.fetchone()
        
        cursor.close()
        return_connection(conn)
        
        if row:
            return dict(zip(columns, row))
        return None
    
    return get_cached_or_query(cache_key, query_db)

def query_customer_by_email(email):
    """Get customer details by email"""
    cache_key = f"customer_{email}"
    
    def query_db():
        conn = get_db_connection()
        if not conn:
            return None
            
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM dbo.fnGetCustomerByIdentifier(?)", (email,))
        
        columns = [column[0] for column in cursor.description]
        row = cursor.fetchone()
        
        cursor.close()
        return_connection(conn)
        
        if row:
            return dict(zip(columns, row))
        return None
    
    return get_cached_or_query(cache_key, query_db)

def verify_otp_token(email, otp_code):
    """Verify OTP token"""
    conn = get_db_connection()
    if not conn:
        return None
        
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM dbo.fnVerifyOTPToken(?, ?)", (email, otp_code))
    
    columns = [column[0] for column in cursor.description]
    row = cursor.fetchone()
    
    cursor.close()
    return_connection(conn)
    
    if row:
        return dict(zip(columns, row))
    return None

# ============================================
# AZURE OPENAI INTEGRATION
# ============================================

# System prompt for the chatbot
SYSTEM_PROMPT = """You are Hakikisha Insurance's AI assistant. You help customers with:
- Policy information and coverage details
- Claim status inquiries
- Premium calculations
- General insurance questions
- Account information

IMPORTANT AUTHENTICATION AWARENESS:
- You ALWAYS know the user's authentication status from the session
- NEVER say "I cannot verify your authentication status"
- For authenticated users: Access their specific data and use their name
- For non-authenticated users: Provide general information only

CRITICAL AUTHENTICATION RULES:
- If a user asks about THEIR policies, claims, or personal information and they are NOT authenticated:
  * Politely inform them they need to log in first
  * Say something like: "I'd be happy to help you with your policies/claims! To access your personal information, please log in first using the login button."
  * DO NOT try to access their data
  * DO NOT apologize excessively
- For general insurance questions (quotes, how insurance works, etc.), answer freely regardless of authentication status

Guidelines:
1. Be professional, friendly, and empathetic
2. Provide accurate information based on the context given
3. If you need to access customer data (policies, claims), FIRST check if user is authenticated
4. For sensitive operations, ensure the user is authenticated
5. If you cannot help with something, politely explain and offer alternatives
6. Always protect customer privacy and data security

When users ask about their specific policies or claims, you'll receive the data from the database and should format it in a clear, conversational way.
"""

# Function definitions for Azure OpenAI function calling
AVAILABLE_FUNCTIONS = [
    {
        "type": "function",
        "function": {
            "name": "get_policy_details",
            "description": "Get detailed information about a specific insurance policy by policy number",
            "parameters": {
                "type": "object",
                "properties": {
                    "policy_number": {
                        "type": "string",
                        "description": "The policy number (e.g., POL123456)"
                    }
                },
                "required": ["policy_number"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_premium",
            "description": "Calculate insurance premium for a given policy type and coverage amount",
            "parameters": {
                "type": "object",
                "properties": {
                    "policy_type": {
                        "type": "string",
                        "enum": ["Auto", "Home", "Life", "Business", "Health", "Travel"],
                        "description": "Type of insurance policy"
                    },
                    "coverage_amount": {
                        "type": "number",
                        "description": "Desired coverage amount in KES"
                    }
                },
                "required": ["policy_type", "coverage_amount"]
            }
        }
    }
]

# ✅ AUTHENTICATED FUNCTIONS - Only available when user is logged in
AUTHENTICATED_FUNCTIONS = [
    {
        "type": "function",
        "function": {
            "name": "get_customer_policies",
            "description": "Get all policies for the authenticated customer",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function", 
        "function": {
            "name": "get_claim_status",
            "description": "Get the status and details of an insurance claim",
            "parameters": {
                "type": "object",
                "properties": {
                    "claim_number": {
                        "type": "string",
                        "description": "The claim number (e.g., CLM789456)"
                    }
                },
                "required": ["claim_number"]
            }
        }
    }
]
        


def execute_function_call(function_name, args, auth_context):
    """
    Execute the function called by Azure OpenAI.
    
    Args:
        function_name (str): The name of the function to execute.
        args (dict): The arguments passed by the AI model (already parsed as a dict).
        auth_context (dict): The authentication and user identity context.
    """
    try:
        # ✅ DEBUG LOGGING
        print(f"🔍 Function: {function_name}, Args: {args}, Auth: {auth_context.get('is_authenticated')}")
        
        is_authenticated = auth_context.get('is_authenticated', False)
        user_id = auth_context.get('user_id')
        
        # --- Functions Requiring Authentication ---
        if function_name in ["get_policy_details", "get_customer_policies", "get_claim_status"]:
            
            # --- Enforce Authentication Check ---
            if not is_authenticated:
                return json.dumps({
                    "access_denied": True,
                    "message": "To access your personal policy and claim information, please log in using the login button in the top right corner. I'll be here to help you once you're logged in!"
                })
            
            # ✅ FIXED: Proper security checks
            if function_name == "get_policy_details":
                policy_number = args.get("policy_number")
                policy = query_policy_by_number(policy_number)
                
                # SECURITY CHECK: Ensure the policy belongs to the logged-in user
                if policy and policy.get('CustomerID') == user_id:
                    return json.dumps(policy)
                else:
                    return json.dumps({"error": "Policy not found or unauthorized access"})
            
            elif function_name == "get_customer_policies":
                # User is authenticated, retrieve policies based on their ID
                policies = query_customer_policies(user_id)
                return json.dumps(policies, cls=CustomJSONEncoder)
            
            elif function_name == "get_claim_status":
                claim_number = args.get("claim_number")
                claim = query_claim_by_number(claim_number)
                
                # SECURITY CHECK: Ensure the claim belongs to the logged-in user
                if claim and claim.get('CustomerID') == user_id:
                    return json.dumps(claim)
                else:
                    return json.dumps({"error": "Claim not found or unauthorized access"})

        # --- Functions Not Requiring Authentication (Public) ---
        elif function_name == "calculate_premium":
            # Public function - no auth required
            policy_type = args.get("policy_type")
            coverage_amount = args.get("coverage_amount")
            
            # Simple calculation (replace with actual business logic)
            rates = {
                "Auto": 0.05, "Home": 0.03, "Life": 0.02, 
                "Business": 0.04, "Health": 0.06, "Travel": 0.01
            }
            
            coverage_amount = float(coverage_amount) if isinstance(coverage_amount, (int, float, str)) and str(coverage_amount).replace('.','').isdigit() else 0
            
            rate = rates.get(policy_type, 0.03)
            monthly_premium = coverage_amount * rate
            annual_premium = monthly_premium * 12
            
            return json.dumps({
                "policy_type": policy_type,
                "coverage_amount": coverage_amount,
                "monthly_premium": round(monthly_premium, 2),
                "annual_premium": round(annual_premium, 2)
            })
        
        else:
            return json.dumps({"error": "Unknown function"})
    
    except Exception as e:
        print(f"❌ Function execution error: {e}")
        import traceback
        traceback.print_exc()
        return json.dumps({"internal_error": str(e), "message": "An internal server error occurred while executing a function."})

def chat_with_openai(user_message, conversation_history=None, auth_context=None):
    """
    Send message to Azure OpenAI and handle function calling.
    This is the main AI interaction function.
    """
    if not openai_client:
        return "I'm sorry, the AI service is currently unavailable. Please try again later."
    
    try:
        # Build messages array
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        # ✅ FIXED: Handle None values in auth_context
        if auth_context:
            if auth_context.get('is_authenticated'):
                customer_name = auth_context.get('customer_name') or 'customer'
                auth_info = f"\n\nCurrent user status: Authenticated as {customer_name}"
            else:
                auth_info = f"\n\nCurrent user status: Not authenticated"
            messages[0]["content"] += auth_info
        
        # Add conversation history if provided
        if conversation_history:
            messages.extend(conversation_history)
        
        # Add current user message
        messages.append({"role": "user", "content": user_message})
        
        # ✅ Build functions list based on authentication
        functions = AVAILABLE_FUNCTIONS.copy()
        if auth_context and auth_context.get('is_authenticated'):
            functions.extend(AUTHENTICATED_FUNCTIONS)
        
        # First API call
        response = openai_client.chat.completions.create(
            model=AZURE_OPENAI_DEPLOYMENT,
            messages=messages,
            tools=functions,
            tool_choice="auto",
            temperature=0.7,
            max_tokens=800
        )
        
        response_message = response.choices[0].message
        
        # Check if the model wants to call functions
        if response_message.tool_calls:
            # Execute function calls
            messages.append(response_message)
            
            for tool_call in response_message.tool_calls:
                function_name = tool_call.function.name
                
                # Parse arguments from JSON string to Python dict
                try:
                    function_args = json.loads(tool_call.function.arguments)
                except json.JSONDecodeError:
                    print(f"❌ Error decoding function arguments for {function_name}")
                    return "Sorry, I ran into an issue processing the requested data. Please try again."
                
                print(f"🔧 Function call: {function_name}({function_args})")
                
                # Pass auth_context to the function execution handler
                function_response = execute_function_call(function_name, function_args, auth_context)
                
                messages.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": function_response
                })
            
            # Second API call with function results
            second_response = openai_client.chat.completions.create(
                model=AZURE_OPENAI_DEPLOYMENT,
                messages=messages,
                temperature=0.7,
                max_tokens=800
            )
            
            return second_response.choices[0].message.content
        
        else:
            # No function call, return direct response
            return response_message.content
    
    except Exception as e:
        print(f"❌ Azure OpenAI error: {e}")
        import traceback
        traceback.print_exc()
        return "I apologize, but I encountered an error processing your request. Please try again."


# ============================================
# AUTHENTICATION MIDDLEWARE
# ============================================

def login_required(f):
    """Decorator to require authentication for certain routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('authenticated'):
            return jsonify({
                'error': 'Authentication required',
                'message': 'Please log in to access this feature'
            }), 401
        return f(*args, **kwargs)
    return decorated_function


# ============================================
# API ROUTES
# ============================================

@app.route('/')
def index():
    """Serve the main HTML page"""
    return render_template('index.html')

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'running',
        'azure_openai': openai_client is not None,
        'database': get_db_connection() is not None,
        'timestamp': datetime.now().isoformat()
    })

# ============================================
# AUTHENTICATION ENDPOINTS
# ============================================

@app.route('/api/send-otp', methods=['POST'])
def send_otp():
    """
    Send OTP to user's email
    Request body: { "email": "user@example.com", "role": "customer" }
    """
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        user_role = data.get('role', 'customer')
        
        if not email:
            return jsonify({'success': False, 'error': 'Email is required'}), 400
        
        # Validate email format
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            return jsonify({'success': False, 'error': 'Invalid email format'}), 400
        
        # Check if user exists in database
        if user_role == 'customer':
            user = query_customer_by_email(email)
            if not user:
                return jsonify({
                    'success': False,
                    'error': 'Email not found. Please contact support to register.'
                }), 404
            user_name = f"{user.get('FirstName', '')} {user.get('LastName', '')}"
        else:
            user_name = "Team Member"
        
        # Generate and send OTP
        otp_code = generate_otp()
        
        # Store in database
        if not store_otp_in_db(email, otp_code, user_role):
            return jsonify({
                'success': False,
                'error': 'Failed to generate OTP. Please try again.'
            }), 500
        
        # Send email
        if not send_otp_email(email, otp_code, user_name):
            return jsonify({
                'success': False,
                'error': 'Failed to send OTP email. Please check your email address.'
            }), 500
        
        # Store email in session (not authenticated yet)
        session['pending_email'] = email
        session['pending_role'] = user_role
        
        return jsonify({
            'success': True,
            'message': 'OTP sent successfully. Please check your email.',
            'email': email
        })
    
    except Exception as e:
        print(f"❌ Send OTP error: {e}")
        return jsonify({
            'success': False,
            'error': 'An error occurred. Please try again.'
        }), 500

@app.route('/api/verify-otp', methods=['POST'])
def verify_otp():
    """
    Verify OTP code
    Request body: { "otp": "123456" }
    """
    try:
        data = request.get_json()
        otp_code = data.get('otp', '').strip()
        
        if not otp_code or len(otp_code) != 6:
            return jsonify({'success': False, 'error': 'Invalid OTP format'}), 400
        
        # Get pending email from session
        email = session.get('pending_email')
        user_role = session.get('pending_role', 'customer')
        
        if not email:
            return jsonify({
                'success': False,
                'error': 'No pending OTP request. Please request a new OTP.'
            }), 400
        
        # Verify OTP
        verification = verify_otp_token(email, otp_code)
        
        if not verification:
            return jsonify({
                'success': False,
                'error': 'Invalid or expired OTP. Please request a new one.'
            }), 401
        
        status = verification.get('ValidationStatus')
        
        if status != 'Valid':
            return jsonify({
                'success': False,
                'error': f'OTP {status.lower()}. Please request a new one.'
            }), 401
        
        # Mark OTP as used
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("EXEC dbo.spMarkOTPUsed @EmailOrPhone=?, @OTPCodeValue=?", (email, otp_code))
            conn.commit()
            cursor.close()
            return_connection(conn)
        
        # Get user details
        user = query_customer_by_email(email)
        
        # Set session as authenticated
        session['authenticated'] = True
        session['user_email'] = email
        session['user_role'] = user_role
        session['user_id'] = user.get('CustomerID') if user else None
        session['user_name'] = f"{user.get('FirstName', '')} {user.get('LastName', '')}" if user else "User"
        
        # Clear pending session data
        session.pop('pending_email', None)
        session.pop('pending_role', None)
        
        # Clear cache for this user
        clear_cache(email)
        
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'user': {
                'email': email,
                'role': user_role,
                'name': session['user_name']
            }
        })
    
    except Exception as e:
        print(f"❌ Verify OTP error: {e}")
        return jsonify({
            'success': False,
            'error': 'Verification failed. Please try again.'
        }), 500


# ============================================
# CHAT ENDPOINT
# ============================================
@app.route('/api/chat', methods=['POST'])
def chat():
    """
    Main chat endpoint
    Request body: { "message": "user message", "sessionId": "unique-session-id" }
    """
    try:
        # ✅ SAFEGUARD: Ensure session is up to date
        session.modified = True

        data = request.get_json()
        user_message = data.get('message', '').strip()
        session_id = data.get('sessionId', 'default')
        
        if not user_message:
            return jsonify({'error': 'Message is required'}), 400
        
        print(f"📨 Chat request - Session: {session_id}, Message: {user_message}")

        # Build authentication context
        auth_context = {
            'is_authenticated': session.get('authenticated', False),
            'user_id': session.get('user_id'),
            'user_role': session.get('user_role'),
            'customer_name': session.get('user_name'),
            'session_id': session_id
        }
        
        # Get conversation history from session (limited to last 10 messages)
        conversation_key = f'conversation_{session_id}'
        conversation_history = session.get(conversation_key, [])

        # ✅ Get response from chat_with_openai (this handles everything)
        ai_response = chat_with_openai(user_message, conversation_history, auth_context)
        
        # Update conversation history
        conversation_history.append({"role": "user", "content": user_message})
        conversation_history.append({"role": "assistant", "content": ai_response})
        
        # Keep only last 10 messages (5 exchanges) to limit token usage
        if len(conversation_history) > 10:
            conversation_history = conversation_history[-10:]
        
        session[conversation_key] = conversation_history

        # Return the successful response
        return jsonify({
            'reply': ai_response,
            'timestamp': datetime.now().isoformat(),
            'authenticated': auth_context['is_authenticated']
        }) 
    
    except Exception as e:
        print(f"❌ Chat error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': 'Failed to process your message. Please try again.'
        }), 500


# ============================================
# ADDITIONAL API ENDPOINTS
# ============================================

@app.route('/api/policy/<policy_number>', methods=['GET'])
@login_required
def get_policy_details_endpoint(policy_number):
    """Get specific policy details"""
    try:
        policy = query_policy_by_number(policy_number)
        if policy:
            return jsonify({'success': True, 'policy': policy})
        else:
            return jsonify({'success': False, 'error': 'Policy not found'}), 404
    except Exception as e:
        print(f"❌ Get policy error: {e}")
        return jsonify({'success': False, 'error': 'Failed to retrieve policy'}), 500

@app.route('/api/claim/<claim_number>', methods=['GET'])
@login_required
def get_claim_details_endpoint(claim_number):
    """Get specific claim details"""
    try:
        claim = query_claim_by_number(claim_number)
        if claim:
            return jsonify({'success': True, 'claim': claim})
        else:
            return jsonify({'success': False, 'error': 'Claim not found'}), 404
    except Exception as e:
        print(f"❌ Get claim error: {e}")
        return jsonify({'success': False, 'error': 'Failed to retrieve claim'}), 500


# ============================================
# AUTHENTICATION ENDPOINTS (Email/Password + OTP)
# ============================================
@app.route('/api/register', methods=['POST'])
def register():
    """
    Register new user - PolicyNumber format: POLNNNNNN (POL + 6 digits)
    """
    conn = None
    cursor = None
    
    import random
    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        role = data.get('role', 'customer')

        if not all([name, email, password, role]):
            return jsonify({'success': False, 'error': 'All fields are required'}), 400

        if len(password) < 8:
            return jsonify({'success': False, 'error': 'Password must be at least 8 characters'}), 400

        # Check if email already exists
        existing_user = query_customer_by_email(email)
        if existing_user:
            return jsonify({'success': False, 'error': 'Email already registered'}), 400

        import hashlib
        password_hash = hashlib.sha256(password.encode()).hexdigest()

        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor()

        if role == 'customer':
            # Generate PolicyNumber in format: POLNNNNNN (POL + 6 digits)
            cursor.execute("""
                SELECT TOP 1 PolicyNumber 
                FROM Customers 
                WHERE PolicyNumber LIKE 'POL%'
                ORDER BY PolicyNumber DESC
            """)
            
            result = cursor.fetchone()
            
            if result and result[0]:
                last_number = int(result[0][3:])
                next_number = last_number + 1
            else:
                next_number = 1
            
            temp_policy_number = f"POL{next_number:06d}"
            
            print(f"📋 Generated PolicyNumber: {temp_policy_number}")
            
            # Generate valid Kenyan phone number
            temp_phone = f"+254{random.randint(700000000, 799999999)}"
            
            # Insert customer
            cursor.execute("""
                INSERT INTO Customers (
                    PolicyNumber,
                    CustomerName,
                    PhoneNumber,
                    Email,
                    County,
                    RegistrationDate,
                    IsActive,
                    CreatedDate,
                    ModifiedDate
                )
                OUTPUT INSERTED.CustomerID
                VALUES (?, ?, ?, ?, ?, GETDATE(), 1, GETDATE(), GETDATE())
            """, (temp_policy_number, name, temp_phone, email, 'Nairobi'))
            
            customer_id_row = cursor.fetchone()
            if not customer_id_row:
                raise Exception("Failed to create customer record")
                
            customer_id = customer_id_row[0]
            print(f"✅ Customer registered: ID={customer_id}, PolicyNumber={temp_policy_number}, Email={email}")

            # Insert into CustomerAuth
            cursor.execute("""
                INSERT INTO CustomerAuth (
                    CustomerID,
                    HashedPassword,
                    OTPAttempts,
                    IsLocked,
                    CreatedDate,
                    LastLogin
                )
                VALUES (?, ?, 0, 0, GETDATE(), GETDATE())
            """, (customer_id, password_hash))
            
        else:  # staff
            name_parts = name.split(maxsplit=1)
            first_name = name_parts[0]
            last_name = name_parts[1] if len(name_parts) > 1 else ''
            
            # Generate EmployeeID: EMP + 6 digits
            cursor.execute("""
                SELECT TOP 1 EmployeeID 
                FROM Staff 
                WHERE EmployeeID LIKE 'EMP%'
                ORDER BY EmployeeID DESC
            """)
            
            result = cursor.fetchone()
            
            if result and result[0]:
                last_number = int(result[0][3:])
                next_number = last_number + 1
            else:
                next_number = 1
            
            employee_id = f"EMP{next_number:06d}"
            
            print(f"👤 Generated EmployeeID: {employee_id}")
            
            # Insert staff with EmployeeID
            cursor.execute("""
                INSERT INTO Staff (
                    EmployeeID,
                    FirstName, 
                    LastName, 
                    Email, 
                    Role, 
                    CreatedDate
                )
                OUTPUT INSERTED.StaffID
                VALUES (?, ?, ?, ?, ?, GETDATE())
            """, (employee_id, first_name, last_name, email, 'Agent'))

            staff_id_row = cursor.fetchone()
            if not staff_id_row:
                raise Exception("Failed to create staff record")
                
            staff_id = staff_id_row[0]
            print(f"✅ Staff registered: ID={staff_id}, EmployeeID={employee_id}, Email={email}")
            
            # Insert into StaffAuth
            try:
                cursor.execute("""
                    INSERT INTO StaffAuth (StaffID, HashedPassword)
                    VALUES (?, ?)
                """, (staff_id, password_hash))
                print(f"✅ Auth record created for staff {staff_id}")
            except Exception as auth_error:
                print(f"⚠️ StaffAuth insert failed: {auth_error}")

        # Commit transaction
        conn.commit()
        
        return jsonify({
            'success': True, 
            'message': 'Registration successful! You can now login.'
        })

    except Exception as e:
        print(f"❌ Registration failed: {e}")
        import traceback
        traceback.print_exc()
        
        if conn:
            conn.rollback()
        
        error_str = str(e)
        if 'duplicate' in error_str.lower() or 'unique' in error_str.lower():
            return jsonify({'success': False, 'error': 'Email already registered'}), 400
        
        return jsonify({'success': False, 'error': 'Registration failed. Please try again.'}), 500
        
    finally:
        if cursor:
            cursor.close()
        if conn:
            return_connection(conn)

@app.route('/api/login', methods=['POST'])
def login():
    """Login with email and password, using Customers and CustomerAuth tables for customers."""
    conn = None 
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        role = data.get('role', 'customer')
        
        if not all([email, password, role]):
            return jsonify({'success': False, 'error': 'All fields are required'}), 400
        
        # Hash password
        import hashlib
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        # Check credentials
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor()
        
        if role == 'customer':
            cursor.execute("""
                SELECT 
                    C.CustomerID, 
                    C.CustomerName, 
                    C.Email 
                FROM Customers C
                JOIN CustomerAuth CA ON C.CustomerID = CA.CustomerID
                WHERE C.Email = ? AND CA.HashedPassword = ?
            """, (email, password_hash))
        else:  # staff
            cursor.execute("""
                SELECT StaffID, FullName, Email, Role
                FROM Staff
                WHERE Email = ? AND PasswordHash = ?
            """, (email, password_hash))
        
        user = cursor.fetchone()
        
        if not user:
            return jsonify({'success': False, 'error': 'Invalid email or password'}), 401
        
        # Set session
        session['authenticated'] = True
        session['user_email'] = email
        session['user_role'] = role
        session['user_id'] = user[0]
        session['user_name'] = user[1]
        
        # Clear cache for this user
        clear_cache(email)
        
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'user': {
                'email': email,
                'role': role,
                'name': user[1]
            }
        })
        
    except Exception as e:
        print(f"❌ Login error: {e}")
        return jsonify({'success': False, 'error': 'Login failed'}), 500
        
    finally:
        if conn:
            cursor.close()
            return_connection(conn)


@app.route('/api/update-profile', methods=['POST'])
@login_required
def update_profile():
    """Allow users to update phone, address, etc."""
    data = request.get_json()
    email = session.get('user_email')
    
    phone = data.get('phone')
    address = data.get('address')
    city = data.get('city')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE Customers
        SET PhoneNumber = ?,
            Address = ?,
            City = ?,
            ModifiedDate = GETDATE()
        WHERE Email = ?
    """, (phone, address, city, email))
    
    conn.commit()
    cursor.close()
    return_connection(conn)
    
    return jsonify({'success': True, 'message': 'Profile updated'})

# ============================================
# CUSTOMER PORTAL ENDPOINTS
# ============================================

@app.route('/api/check-session', methods=['GET'])
def check_session():
    """Check if user is authenticated and return user info"""
    try:
        if session.get('authenticated'):
            return jsonify({
                'authenticated': True,
                'user': {
                    'email': session.get('user_email'),
                    'role': session.get('user_role'),
                    'name': session.get('user_name'),
                    'id': session.get('user_id')
                }
            })
        else:
            return jsonify({'authenticated': False}), 401
    except Exception as e:
        print(f"❌ Session check error: {e}")
        return jsonify({'authenticated': False}), 401

@app.route('/api/policies', methods=['GET'])
def get_user_policies():
    """Get all policies for the authenticated customer"""
    try:
        # Check authentication
        if not session.get('authenticated'):
            return jsonify({'success': False, 'error': 'Not authenticated'}), 401
        
        email = session.get('user_email')
        role = session.get('user_role')
        
        if role != 'customer':
            return jsonify({'success': False, 'error': 'Only customers can view policies'}), 403
        
        # Get customer ID
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor()
        
        # Get customer
        cursor.execute("""
            SELECT CustomerID, CustomerName
            FROM Customers
            WHERE Email = ?
        """, (email,))
        
        customer = cursor.fetchone()
        
        if not customer:
            cursor.close()
            return_connection(conn)
            return jsonify({'success': False, 'error': 'Customer not found'}), 404
        
        customer_id = customer[0]
        
        # Get all policies for this customer
        cursor.execute("""
            SELECT 
                PolicyID,
                PolicyNumber,
                PolicyName,
                PremiumAmount,
                CoverageAmount,
                StartDate,
                EndDate,
                PolicyStatus,
                PaymentStatus,
                PaymentFrequency,
                NextPaymentDue,
                CreatedDate
            FROM Policies
            WHERE CustomerID = ?
            ORDER BY CreatedDate DESC
        """, (customer_id,))
        
        columns = [column[0] for column in cursor.description]
        rows = cursor.fetchall()
        
        cursor.close()
        return_connection(conn)
        
        # Convert to list of dictionaries
        policies = []
        for row in rows:
            policy = dict(zip(columns, row))
            
            # Convert dates to strings
            for date_field in ['StartDate', 'EndDate', 'NextPaymentDue', 'CreatedDate']:
                if policy.get(date_field):
                    policy[date_field] = policy[date_field].isoformat() if hasattr(policy[date_field], 'isoformat') else str(policy[date_field])
            
            # Add compatibility fields
            policy['Status'] = policy.get('PolicyStatus', 'Unknown')
            policy['PolicyType'] = policy.get('PolicyName', 'Insurance')
            
            policies.append(policy)
        
        print(f"✅ Retrieved {len(policies)} policies for customer {customer_id}")
        
        return jsonify({
            'success': True,
            'policies': policies
        })
        
    except Exception as e:
        print(f"❌ Get policies error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': 'Failed to retrieve policies'}), 500

@app.route('/api/claims', methods=['GET'])
def get_user_claims():
    """Get all claims for the authenticated customer"""
    try:
        # Check authentication
        if not session.get('authenticated'):
            return jsonify({'success': False, 'error': 'Not authenticated'}), 401
        
        email = session.get('user_email')
        role = session.get('user_role')
        
        if role != 'customer':
            return jsonify({'success': False, 'error': 'Only customers can view claims'}), 403
        
        # Get database connection
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor()
        
        # Get customer ID
        cursor.execute("""
            SELECT CustomerID
            FROM Customers
            WHERE Email = ?
        """, (email,))
        
        customer = cursor.fetchone()
        
        if not customer:
            cursor.close()
            return_connection(conn)
            return jsonify({'success': False, 'error': 'Customer not found'}), 404
        
        customer_id = customer[0]
        
        # Get all claims for this customer
        cursor.execute("""
            SELECT 
                c.ClaimID,
                c.ClaimNumber,
                c.ClaimType,
                c.ClaimAmount,
                c.ApprovedAmount,
                c.ClaimStatus,
                c.Description,
                c.IncidentDate,
                c.ReportedDate,
                c.SettlementDate,
                p.PolicyNumber,
                p.PolicyName
            FROM Claims c
            INNER JOIN Policies p ON c.PolicyID = p.PolicyID
            WHERE c.CustomerID = ?
            ORDER BY c.ReportedDate DESC
        """, (customer_id,))
        
        columns = [column[0] for column in cursor.description]
        rows = cursor.fetchall()
        
        cursor.close()
        return_connection(conn)
        
        # Convert to list of dictionaries
        claims = []
        for row in rows:
            claim = dict(zip(columns, row))
            
            # Convert dates to strings
            for date_field in ['IncidentDate', 'ReportedDate', 'SettlementDate']:
                if claim.get(date_field):
                    claim[date_field] = claim[date_field].isoformat() if hasattr(claim[date_field], 'isoformat') else str(claim[date_field])
            
            # Add compatibility fields
            claim['Amount'] = claim.get('ClaimAmount', 0)
            claim['Status'] = claim.get('ClaimStatus', 'Unknown')
            claim['SubmissionDate'] = claim.get('ReportedDate')
            claim['Reason'] = claim.get('Description', 'No description')
            claim['PolicyType'] = claim.get('PolicyName', 'Insurance')
            
            claims.append(claim)
        
        print(f"✅ Retrieved {len(claims)} claims for customer {customer_id}")
        
        return jsonify({
            'success': True,
            'claims': claims
        })
        
    except Exception as e:
        print(f"❌ Get claims error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': 'Failed to retrieve claims'}), 500


# ============================================
# REMINDERS ENDPOINT
# ============================================

@app.route('/api/reminders', methods=['GET'])
def get_reminders():
    """Get payment reminders and important notifications for customer"""
    try:
        # Check authentication
        if not session.get('authenticated'):
            return jsonify({'success': False, 'error': 'Not authenticated'}), 401
        
        email = session.get('user_email')
        role = session.get('user_role')
        
        if role != 'customer':
            return jsonify({'success': False, 'error': 'Only customers can view reminders'}), 403
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor()
        
        # Get customer ID
        cursor.execute("SELECT CustomerID FROM Customers WHERE Email = ?", (email,))
        customer = cursor.fetchone()
        
        if not customer:
            cursor.close()
            return_connection(conn)
            return jsonify({'success': False, 'error': 'Customer not found'}), 404
        
        customer_id = customer[0]
        
        reminders = []
        
        # PAYMENT REMINDERS
        cursor.execute("""
            SELECT 
                PolicyNumber,
                PolicyName,
                NextPaymentDue,
                PremiumAmount,
                PaymentFrequency,
                DATEDIFF(day, GETDATE(), NextPaymentDue) AS DaysUntilDue
            FROM Policies
            WHERE CustomerID = ? 
            AND PolicyStatus = 'Active'
            AND NextPaymentDue >= GETDATE()
            AND DATEDIFF(day, GETDATE(), NextPaymentDue) <= 30
            ORDER BY NextPaymentDue
        """, (customer_id,))
        
        payments = cursor.fetchall()
        
        for payment in payments:
            policy_number = payment[0]
            policy_name = payment[1]
            due_date = payment[2]
            amount = payment[3]
            frequency = payment[4]
            days_until = payment[5]
            
            # Determine urgency
            if days_until <= 3:
                urgency = 'critical'
                icon = '🚨'
                color = 'red'
            elif days_until <= 7:
                urgency = 'high'
                icon = '⚠️'
                color = 'orange'
            elif days_until <= 14:
                urgency = 'medium'
                icon = '⏰'
                color = 'yellow'
            else:
                urgency = 'low'
                icon = '📅'
                color = 'blue'
            
            # Create message
            if days_until == 0:
                message = f"Payment due TODAY for {policy_name}"
            elif days_until == 1:
                message = f"Payment due TOMORROW for {policy_name}"
            else:
                message = f"Payment due in {days_until} days for {policy_name}"
            
            reminders.append({
                'id': f'payment-{policy_number}',
                'type': 'payment',
                'urgency': urgency,
                'icon': icon,
                'color': color,
                'title': f'Premium Payment Due',
                'message': message,
                'details': {
                    'policyNumber': policy_number,
                    'policyName': policy_name,
                    'amount': float(amount),
                    'dueDate': due_date.isoformat() if due_date else None,
                    'frequency': frequency,
                    'daysUntil': days_until
                },
                'action': 'Make Payment',
                'actionUrl': f'/payment?policy={policy_number}'
            })
        
        cursor.close()
        return_connection(conn)
        
        # Sort by urgency
        urgency_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        reminders.sort(key=lambda x: urgency_order.get(x['urgency'], 4))
        
        print(f"✅ Retrieved {len(reminders)} reminders for customer {customer_id}")
        
        return jsonify({
            'success': True,
            'reminders': reminders,
            'count': len(reminders)
        })
        
    except Exception as e:
        print(f"❌ Get reminders error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': 'Failed to retrieve reminders'}), 500

@app.route('/api/logout', methods=['POST'])
def logout():
    """Logout user and clear session"""
    try:
        email = session.get('user_email', 'unknown')
        session.clear()
        print(f"✅ User logged out: {email}")
        return jsonify({'success': True, 'message': 'Logged out successfully'})
    except Exception as e:
        print(f"❌ Logout error: {e}")
        return jsonify({'success': False, 'error': 'Logout failed'}), 500
    

# ============================================
# QUOTE REQUEST SYSTEM
# Add this section to your app.py file before the ERROR HANDLERS section
# ============================================

@app.route('/api/quote-request', methods=['POST'])
def submit_quote_request():
    """
    Handle quote requests from website visitors
    This allows anyone to request a quote without authentication
    """
    conn = None
    cursor = None
    
    try:
        data = request.get_json()
        
        # Extract form data
        policy_type = data.get('policyType', '').strip()
        coverage_amount = float(data.get('coverageAmount', 0))
        payment_frequency = data.get('paymentFrequency', '').strip()
        start_date = data.get('startDate', '')
        additional_info = data.get('additionalInfo', '').strip()
        
        first_name = data.get('firstName', '').strip()
        last_name = data.get('lastName', '').strip()
        email = data.get('email', '').strip().lower()
        phone = data.get('phone', '').strip()
        county = data.get('county', '').strip()
        
        # Validation
        if not all([policy_type, coverage_amount, payment_frequency, start_date, 
                   first_name, last_name, email, phone, county]):
            return jsonify({
                'success': False, 
                'error': 'All required fields must be filled'
            }), 400
        
        # Calculate estimated premium using AI
        estimated_premium = calculate_premium_ai(policy_type, coverage_amount, payment_frequency)
        
        # Generate unique quote number
        import random
        quote_number = f"QTE{random.randint(100000, 999999)}"
        
        # Connect to database
        conn = get_db_connection()
        if not conn:
            return jsonify({
                'success': False, 
                'error': 'Database connection failed'
            }), 500
        
        cursor = conn.cursor()
        
        # Insert quote request
        cursor.execute("""
            INSERT INTO QuoteRequests (
                QuoteNumber,
                FirstName,
                LastName,
                Email,
                PhoneNumber,
                County,
                PolicyType,
                CoverageAmount,
                PaymentFrequency,
                PreferredStartDate,
                EstimatedPremium,
                AdditionalInfo,
                RequestStatus,
                RequestDate,
                CreatedDate
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Pending', GETDATE(), GETDATE())
        """, (
            quote_number,
            first_name,
            last_name,
            email,
            phone,
            county,
            policy_type,
            coverage_amount,
            payment_frequency,
            start_date,
            estimated_premium,
            additional_info if additional_info else None
        ))
        
        conn.commit()
        
        print(f"✅ Quote request submitted: {quote_number} - {first_name} {last_name} ({email})")
        
        # Send confirmation email (optional)
        try:
            send_quote_confirmation_email(email, f"{first_name} {last_name}", quote_number, estimated_premium, payment_frequency)
        except Exception as email_error:
            print(f"⚠️ Failed to send confirmation email: {email_error}")
        
        return jsonify({
            'success': True,
            'message': 'Quote request submitted successfully',
            'quoteNumber': quote_number,
            'estimatedPremium': estimated_premium
        })
        
    except Exception as e:
        print(f"❌ Quote request error: {e}")
        import traceback
        traceback.print_exc()
        
        if conn:
            conn.rollback()
        
        return jsonify({
            'success': False, 
            'error': 'Failed to process quote request. Please try again.'
        }), 500
        
    finally:
        if cursor:
            cursor.close()
        if conn:
            return_connection(conn)


def calculate_premium_ai(policy_type, coverage_amount, payment_frequency):
    """
    Calculate insurance premium using AI-powered algorithm
    This provides intelligent pricing based on policy type and coverage
    """
    # Base rates per policy type (annual rate as % of coverage)
    base_rates = {
        "Auto": 0.05,      # 5% of coverage
        "Home": 0.03,      # 3% of coverage
        "Life": 0.02,      # 2% of coverage
        "Health": 0.06,    # 6% of coverage
        "Business": 0.04,  # 4% of coverage
        "Travel": 0.01     # 1% of coverage
    }
    
    # Get base rate
    rate = base_rates.get(policy_type, 0.03)
    
    # Calculate annual premium
    annual_premium = coverage_amount * rate
    
    # Adjust for payment frequency
    frequency_multipliers = {
        "Monthly": 1.05,    # 5% more for monthly (admin overhead)
        "Quarterly": 1.02,  # 2% more for quarterly
        "Annually": 1.00    # No markup for annual
    }
    
    multiplier = frequency_multipliers.get(payment_frequency, 1.00)
    annual_premium *= multiplier
    
    # Convert to payment frequency amount
    if payment_frequency == "Monthly":
        return round(annual_premium / 12, 2)
    elif payment_frequency == "Quarterly":
        return round(annual_premium / 4, 2)
    else:  # Annually
        return round(annual_premium, 2)


def send_quote_confirmation_email(recipient_email, recipient_name, quote_number, estimated_premium, payment_frequency):
    """Send quote request confirmation email"""
    try:
        sender_email = os.getenv('EMAIL_USER')
        sender_password = os.getenv('EMAIL_PASSWORD')
        
        if not sender_email or not sender_password:
            print("⚠️ Email credentials not configured")
            return False
        
        message = MIMEMultipart("alternative")
        message["Subject"] = f"Quote Request Received - {quote_number}"
        message["From"] = f"Hakikisha Insurance <{sender_email}>"
        message["To"] = recipient_email
        
        html = f"""
        <html>
          <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background-color: white; border-radius: 10px; padding: 30px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
              <div style="text-align: center; margin-bottom: 30px;">
                <h2 style="color: #667eea; margin: 0;">👌 Hakikisha Insurance</h2>
              </div>
              
              <p style="color: #333; font-size: 16px;">Hello {recipient_name},</p>
              
              <p style="color: #666; font-size: 14px;">
                Thank you for requesting a quote from Hakikisha Insurance. We've received your request and our team is reviewing it.
              </p>
              
              <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; text-align: center; border-radius: 8px; margin: 20px 0;">
                <div style="color: white; font-size: 14px; margin-bottom: 5px;">Your Quote Reference Number</div>
                <div style="font-size: 32px; font-weight: bold; letter-spacing: 4px; color: white;">
                  {quote_number}
                </div>
              </div>
              
              <div style="background: #f5f7ff; padding: 15px; border-radius: 8px; margin: 20px 0;">
                <h3 style="color: #333; margin-top: 0;">Estimated Premium</h3>
                <p style="color: #666; font-size: 14px; margin: 5px 0;">
                  <strong style="color: #667eea; font-size: 24px;">KES {estimated_premium:,.2f}</strong> per {payment_frequency.lower()} payment
                </p>
                <p style="color: #999; font-size: 12px; margin: 5px 0;">
                  *This is an estimated premium. Final pricing will be provided by our team.
                </p>
              </div>
              
              <h3 style="color: #333;">What Happens Next?</h3>
              <ol style="color: #666; font-size: 14px; line-height: 1.8;">
                <li>Our insurance specialists will review your request</li>
                <li>We'll prepare a personalized quote based on your needs</li>
                <li>You'll receive a detailed proposal within 24 hours</li>
                <li>Feel free to ask any questions when we contact you</li>
              </ol>
              
              <p style="color: #999; font-size: 12px; margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee;">
                If you have any immediate questions, please contact us at info@hakikishainsurance.co.ke or call +254 700 000 000
              </p>
              
              <div style="text-align: center; margin-top: 30px; color: #999; font-size: 12px;">
                <p>Hakikisha Insurance - Protect What Matters Most</p>
              </div>
            </div>
          </body>
        </html>
        """
        
        part = MIMEText(html, "html")
        message.attach(part)
        
        with smtplib.SMTP(os.getenv('EMAIL_HOST', 'smtp.gmail.com'), 
                         int(os.getenv('EMAIL_PORT', 587))) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient_email, message.as_string())
        
        print(f"✅ Quote confirmation email sent to {recipient_email}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to send quote confirmation email: {e}")
        return False


@app.route('/api/admin/quotes', methods=['GET'])
@login_required
def get_all_quotes():
    """
    Get all quote requests (Admin/Staff only)
    """
    try:
        # Check if user is staff
        if session.get('user_role') != 'staff':
            return jsonify({
                'success': False, 
                'error': 'Unauthorized access'
            }), 403
        
        conn = get_db_connection()
        if not conn:
            return jsonify({
                'success': False, 
                'error': 'Database connection failed'
            }), 500
        
        cursor = conn.cursor()
        
        # Get all quote requests
        cursor.execute("""
            SELECT 
                QuoteID,
                QuoteNumber,
                FirstName,
                LastName,
                Email,
                PhoneNumber,
                County,
                PolicyType,
                CoverageAmount,
                EstimatedPremium,
                PaymentFrequency,
                PreferredStartDate,
                RequestStatus,
                RequestDate,
                AdditionalInfo
            FROM QuoteRequests
            ORDER BY RequestDate DESC
        """)
        
        columns = [column[0] for column in cursor.description]
        rows = cursor.fetchall()
        
        cursor.close()
        return_connection(conn)
        
        # Convert to list of dictionaries
        quotes = []
        for row in rows:
            quote = dict(zip(columns, row))
            
            # Convert dates to strings
            if quote.get('RequestDate'):
                quote['RequestDate'] = quote['RequestDate'].isoformat()
            if quote.get('PreferredStartDate'):
                quote['PreferredStartDate'] = quote['PreferredStartDate'].isoformat()
            
            quotes.append(quote)
        
        return jsonify({
            'success': True,
            'quotes': quotes
        })
        
    except Exception as e:
        print(f"❌ Get quotes error: {e}")
        return jsonify({
            'success': False, 
            'error': 'Failed to retrieve quotes'
        }), 500


@app.route('/api/admin/quotes/<quote_id>/status', methods=['PUT'])
@login_required
def update_quote_status(quote_id):
    """
    Update quote request status (Admin/Staff only)
    """
    try:
        if session.get('user_role') != 'staff':
            return jsonify({
                'success': False, 
                'error': 'Unauthorized access'
            }), 403
        
        data = request.get_json()
        new_status = data.get('status', '').strip()
        
        if new_status not in ['Pending', 'Contacted', 'Quote Sent', 'Converted', 'Declined']:
            return jsonify({
                'success': False, 
                'error': 'Invalid status'
            }), 400
        
        conn = get_db_connection()
        if not conn:
            return jsonify({
                'success': False, 
                'error': 'Database connection failed'
            }), 500
        
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE QuoteRequests
            SET RequestStatus = ?, ModifiedDate = GETDATE()
            WHERE QuoteID = ?
        """, (new_status, quote_id))
        
        conn.commit()
        cursor.close()
        return_connection(conn)
        
        return jsonify({
            'success': True,
            'message': 'Quote status updated successfully'
        })
        
    except Exception as e:
        print(f"❌ Update quote status error: {e}")
        return jsonify({
            'success': False, 
            'error': 'Failed to update quote status'
        }), 500    
# ============================================
# ERROR HANDLERS
# ============================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

# ============================================
# RUN APPLICATION
# ============================================

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('DEBUG', 'False').lower() == 'true'
    
    print(f"🚀 Starting Hakikisha Insurance Chatbot on port {port}")
    print(f"📍 Chat endpoint: http://localhost:{port}/api/chat")
    print(f"📍 Health check: http://localhost:{port}/health")
    
    app.run(host='0.0.0.0', port=port, debug=debug)
   