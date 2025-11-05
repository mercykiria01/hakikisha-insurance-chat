require('dotenv').config(); // Load .env variables




const express = require('express');
const app = express();
app.use(express.json());
const { SessionsClient } = require('@google-cloud/dialogflow');

const bcrypt = require('bcryptjs');
const { v4: uuidv4 } = require('uuid');
// const { CosmosClient } = require('@azure/cosmos');
const bodyParser = require('body-parser');
const nodemailer = require('nodemailer');
const sql = require('mssql');

// Middleware
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));
app.use(express.static(__dirname));

// Add CORS headers for Dialogflow
app.use((req, res, next) => {
  res.header('Access-Control-Allow-Origin', '*');
  res.header('Access-Control-Allow-Headers', 'Origin, X-Requested-With, Content-Type, Accept');
  next();
});



// Connect to Cosmos DB (SQL API)

//const endpoint = process.env.COSMOS_CONNECTION_STRING;

//const key = process.env.COSMOS_KEY;

//const dbName = process.env.COSMOS_DB_NAME;



//const client = new CosmosClient({ endpoint, key });



//let usersContainer, adminsContainer, customersContainer;



//async function connectDB() {

//try {

//const { database } = await client.databases.createIfNotExists({ id: dbName });



//const { container: users } = await database.containers.createIfNotExists({ id: "Users" });

//const { container: admins } = await database.containers.createIfNotExists({ id: "Admins" });

//const { container: customers } = await database.containers.createIfNotExists({ id: "Customers" });



//usersContainer = users;

//adminsContainer = admins;

//customersContainer = customers;



//console.log("✅ Connected to Azure Cosmos DB (SQL API)");

//} catch (error) {

//console.error("❌ DB connection error:", error);

//process.exit(1);

//}

//}

//connectDB();



// ================== REGISTRATION ==================

// Setup nodemailer transporter (use your email credentials)

//const transporter = nodemailer.createTransport({

//service: 'gmail',

//auth: {

//user: 'your-email@gmail.com',      // your Gmail address

//pass: 'your-app-password'          // your Gmail App Password

//}

//});



//app.post('/register', async (req, res) => {

//try {

//const { name, email, password, role } = req.body;

//if (!name || !email || !password || !role) {

//return res.status(400).json({ error: "All fields are required" });

//}



// Check if user exists

//const result = await sql.query`SELECT * FROM Users WHERE email = ${email}`;

//if (result.recordset.length > 0) {

//return res.status(400).json({ error: "Email already exists" });

//}



//const hashedPassword = await bcrypt.hash(password, 10);

//const otp = Math.floor(100000 + Math.random() * 900000).toString();



//await sql.query`

//INSERT INTO Users (id, name, email, password, role, otp, verified)

//VALUES (${uuidv4()}, ${name}, ${email}, ${hashedPassword}, ${role}, ${otp}, 0)

//`;



// Send OTP email

//await transporter.sendMail({

//from: 'your-email@gmail.com',

//to: email,

//subject: 'Your Hakikisha Insurance OTP',

//text: `Hello ${name},\n\nYour OTP for account verification is: ${otp}\n\nPlease enter this code to verify your account.`

//});



//res.status(201).json({ message: "User registered successfully" });

//} catch (error) {

//console.error("❌ Registration error:", error);

//res.status(500).json({ error: "Server error" });

//}

//});



// ================== LOGIN ==================

//app.post('/login', async (req, res) => {
//  try {
  //  const { email, password } = req.body;
    //if (!email || !password) {
      //return res.status(400).json({ error: "Email and password are required" });
    //}

    //const result = await sql.query`SELECT * FROM Users WHERE email = ${email}`;
    //const user = result.recordset[0];

    //if (!user) {
      //return res.status(400).json({ error: "Invalid credentials" });
    //}
    //if (!user.verified) {
      //return res.status(403).json({ error: "Please verify your account with the OTP sent to your email." });
    //}

    //const isMatch = await bcrypt.compare(password, user.password);
    //if (!isMatch) {
      //return res.status(400).json({ error: "Invalid credentials" });
    //}

    //res.status(200).json({ message: "Login successful", role: user.role });
  //} catch (error) {
    //console.error("❌ Login error:", error);
    //res.status(500).json({ error: "Server error" });
  //}
//});

// ================== OTP VERIFICATION ==================

//app.post('/verify-otp', async (req, res) => {
  //const { email, otp } = req.body;
  //try {
    //const result = await sql.query`SELECT * FROM Users WHERE email = ${email}`;
    //const user = result.recordset[0];
    //if (!user) return res.status(400).json({ error: "User not found" });
    //if (user.verified) return res.status(400).json({ error: "Already verified" });
    //if (user.otp !== otp) return res.status(400).json({ error: "Invalid OTP" });

    //await sql.query`UPDATE Users SET verified = 1 WHERE email = ${email}`;
    //res.json({ message: "Verification successful" });
  //} catch (error) {
    //res.status(500).json({ error: "Server error" });
  //}
//});

// Azure SQL config
const config = {
  user: process.env.DB_USER,
  password: process.env.DB_PASSWORD,
  server: process.env.DB_SERVER,
  database: process.env.DB_DATABASE,
  options: {
    encrypt: true,                 // required for Azure
    trustServerCertificate: true
       // set true for local testing only
  },
  connectionTimeout: 30000,        // 30s
  requestTimeout: 30000
};

// Dialogflow Configuration
const DIALOGFLOW_PROJECT_ID = process.env.DIALOGFLOW_PROJECT_ID;
const DIALOGFLOW_LANGUAGE_CODE = 'en';

// Initialize Dialogflow client
// Make sure GOOGLE_APPLICATION_CREDENTIALS env var points to your service account key
const sessionClient = new SessionsClient();


// Middleware for parsing JSON and handling HTTPS
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

const axios = require('axios');

// Proxy endpoint to call Flask API
app.post('/api/ask-faq', async (req, res) => {
  console.log('DEBUG /api/ask-faq received body:', req.body);
  try {
    const { question, customer_id, k } = req.body || {};
    if (!question || typeof question !== 'string' || !question.trim()) {
      return res.status(400).json({ error: 'Missing or invalid "question" in request body' });
    }

    const flaskUrl = process.env.FLASK_API_URL;
    if (!flaskUrl) {
      console.error('FLASK_API_URL not set');
      return res.status(500).json({ error: 'FLASK_API_URL not configured on server' });
    }

    const forwardHeaders = {
      'Content-Type': 'application/json',
      Accept: 'application/json'
    };
    if (req.headers.authorization) forwardHeaders.Authorization = req.headers.authorization;

    const payload = { question: question.trim() };
    if (customer_id) payload.customer_id = customer_id;
    if (k) payload.k = k;

    const response = await axios.post(flaskUrl, payload, {
      headers: forwardHeaders,
      timeout: 15000
    });

    return res.status(response.status).json({
      source: 'flask',
      ...response.data
    });

  } catch (error) {
    // improved debug logs
    console.error('❌ Error calling Flask API (proxy):', error.message);
    if (error.response) {
      console.error('Flask response status:', error.response.status);
      console.error('Flask response data:', JSON.stringify(error.response.data));
      return res.status(error.response.status).json({
        error: 'Flask API error',
        details: error.response.data
      });
    }
    console.error(error.stack);
    if (error.code === 'ECONNABORTED') {
      return res.status(504).json({ error: 'Flask API timeout' });
    }
    return res.status(502).json({ error: 'Failed to fetch response from Flask API', details: error.message });
  }
});


// Add CORS headers for Dialogflow
app.use((req, res, next) => {
  res.header('Access-Control-Allow-Origin', '*');
  res.header('Access-Control-Allow-Headers', 'Origin, X-Requested-With, Content-Type, Accept');
  next();
});



// Add a root endpoint for basic testing
app.get('/', (req, res) => {
  console.log('GET request to root');
  res.json({ 
    status: 'Server is running',
    webhook_url: '/webhook',
    timestamp: new Date().toISOString()
  });
});



// Webhook endpoint for Dialogflow with enhanced debugging
app.get('/webhook', (req, res) => {
  console.log('GET request to /webhook - webhook is accessible');
  res.json({ 
    status: 'Webhook is working',
    timestamp: new Date().toISOString()
  });
});

let pool = null;
const poolPromise = sql.connect(config)
  .then(p => {
    console.log('✅ Connected to Azure SQL');
    pool = p;
    return p;
  })
  .catch(err => {
    console.error('❌ Failed to connect to Azure SQL:', err);
    pool = null;
    return null;
  });


  
// ============================================
// FRONTEND CHAT ENDPOINT
// ============================================
app.post('/chat', async (req, res) => {
  const { message, sessionId } = req.body;

  if (!message || !sessionId) {
    return res.status(400).json({ 
      error: 'Message and sessionId are required' 
    });
  }

  console.log(`📨 Chat request - Session: ${sessionId}, Message: ${message}`);

  try {
    // Create Dialogflow session path
    const sessionPath = sessionClient.projectAgentSessionPath(
      DIALOGFLOW_PROJECT_ID,
      sessionId
    );

      // Prepare the request for Dialogflow
    const request = {
      session: sessionPath,
      queryInput: {
        text: {
          text: message,
          languageCode: DIALOGFLOW_LANGUAGE_CODE,
        },
      },
    };

    
    // Send request to Dialogflow
    const [response] = await sessionClient.detectIntent(request);
    const result = response.queryResult;

    console.log(`✅ Dialogflow response - Intent: ${result.intent?.displayName}`);
    console.log(`   Fulfillment: ${result.fulfillmentText}`);

    // Return the response to frontend
    return res.json({
      reply: result.fulfillmentText,
      intent: result.intent?.displayName,
      confidence: result.intentDetectionConfidence
    });

  } catch (error) {
    console.error('❌ Error in /chat endpoint:', error);
    return res.status(500).json({ 
      error: 'Failed to process your message',
      details: error.message 
    });
  }
});

// Webhook endpoint for Dialogflow with enhanced debugging
app.post('/webhook', async (req, res) => {
  // Add comprehensive logging to debug the issue
  console.log('=== WEBHOOK REQUEST DEBUG ===');
  console.log('Full request body:', JSON.stringify(req.body, null, 2));
  
  // Check if the request structure is what we expect
  if (!req.body || !req.body.queryResult) {
    console.log('ERROR: Missing queryResult in request body');
    return res.json({ fulfillmentText: 'Invalid request structure.' });
  }

  
  const intent = req.body.queryResult.intent.displayName;
  const parameters = req.body.queryResult.parameters;
  const queryResult = req.body.queryResult;
  const contexts = queryResult.outputContexts || [];
  const queryText = queryResult.queryText;

  console.log('Intent:', intent);
  console.log('Parameters:', parameters);
  console.log('Contexts:', contexts.map(c => c.name.split('/').pop()));

  if (!req.body.queryResult.intent) {
    console.log('ERROR: Missing intent in queryResult');
    return res.json({ fulfillmentText: 'No intent found in request.' });
  }


  
  console.log('Intent received:', intent);
  console.log('Parameters received:', JSON.stringify(parameters, null, 2));
  console.log('Intent type:', typeof intent);
  console.log('Intent length:', intent?.length);
  
  // Check for common issues
  if (!intent) {
    console.log('ERROR: Intent is null or undefined');
    return res.json({ fulfillmentText: 'Intent is missing.' });
  }

  try {
    // Connect to SQL (use a pool for production)
    if (!pool) {
      console.log('Waiting for database pool to be ready...');
      await poolPromise;
      if (!pool) {
        throw new Error('Database connection pool not available');
      }
    }


     // Extract role context
    const roleContext = getRoleContext(contexts);
    console.log('Active Role:', roleContext);

    // Route to appropriate handler based on intent
    let responseText = '';

    switch (intent) {
      case 'PolicyDetails':
      case 'check.policy.status':
        responseText = await handlePolicyDetails(parameters, queryText, roleContext);
        break;

      case 'GeneralFAQ':
        responseText = await handleGeneralFAQ(parameters, queryText, roleContext);
        break;

      case 'ComplexClaimQuery':
        responseText = await handleComplexClaimQuery(parameters, queryText, roleContext);
        break;

      case 'DocumentVerification':
        responseText = await handleDocumentVerification(parameters, queryText, roleContext);
        break;

      case 'ClaimStatus':
        responseText = await handleClaimStatus(parameters, queryText, roleContext);
        break;

      default:
        responseText = `I understand you're asking about "${intent}", but I need more specific information to help you.`;
    }

    console.log('✅ Sending response:', responseText);
    return res.json({ fulfillmentText: responseText });

  } catch (error) {
    console.error('❌ Webhook error:', error);
    return res.json({ 
      fulfillmentText: 'Sorry, I encountered an error processing your request. Please try again.' 
    });
  }
});



// ============================================
// HELPER FUNCTIONS
// ============================================

function getRoleContext(contexts) {
  for (const context of contexts) {
    const contextName = context.name.split('/').pop();
    if (contextName.includes('customer-mode')) return 'customer';
    if (contextName.includes('visitor-mode')) return 'visitor';
    if (contextName.includes('staff-mode')) return 'staff';
  }
  return 'unknown';
}


// ============================================
// INTENT HANDLERS
// ============================================

async function handlePolicyDetails(parameters, queryText, roleContext) {
  console.log('📋 Handling PolicyDetails intent');

  // Check authorization
  if (roleContext === 'visitor') {
    return "I'm sorry, but policy details are only available to customers and staff. Please select your role first.";
  }


   // Extract policy number - try multiple parameter variations
  const policyNumber = parameters['policy-number'] || 
                       parameters['policynumber'] || 
                       parameters['number'] ||
                       parameters['any'] ||
                       extractPolicyNumber(queryText);

  console.log('Extracted policy number:', policyNumber);

    
  if (!policyNumber) {
    return 'Please provide a valid policy number (e.g., POL123456).';
  }

   try {
    // Query Azure SQL
    console.log('Querying database for policy:', policyNumber);
    
    const result = await pool.request()
      .input('policyNumber', sql.VarChar, policyNumber)
      .query('SELECT * FROM fn_GetPolicyDetails(@policyNumber)');

    const policy = result.recordset[0];

    if (!policy) {
      console.log('❌ No policy found for:', policyNumber);
      return `No policy found with number ${policyNumber}.`;
    }

    console.log('✅ Policy found:', policy);


  
    // Format response based on role
  if (roleContext === 'staff') {
      return `Policy ${policy.PolicyName} (${policyNumber}):\n` +
             `Type: ${policy.PolicyType}\n` +
             `Holder: ${policy.HolderName}\n` +
             `Status: ${policy.Status}\n` +
             `Valid until: ${policy.EndDate}\n` +
             `Premium: $${policy.PremiumAmount}`;
    } 
    else {
      return `Your policy ${policy.PolicyName} covers ${policy.PolicyType} and is valid until ${policy.EndDate}. Premium: $${policy.PremiumAmount}/month.`;
    }
  }
    catch (error) {
    console.error('❌ Database error in handlePolicyDetails:', error);
    throw error;
  }
}
    

// General FAQ handler
async function handleGeneralFAQ(parameters, queryText, roleContext) {
  console.log('❓ Handling GeneralFAQ intent');

  try {
    // Call Flask RAG API
    const response = await axios.post(`${FLASK_RAG_URL}/query`, {
      question: queryText,
      role: roleContext
    }, {
      timeout: 10000 // 10 second timeout
    });

    return response.data.answer || "I couldn't find information about that. Could you rephrase your question?";

  } catch (error) {
    console.error('Flask RAG API error:', error);
    return "I'm having trouble accessing that information right now. Please try again or contact support.";
  }
}

// Complex Claim Query handler
async function handleComplexClaimQuery(parameters, queryText, roleContext) {
  console.log('🔍 Handling ComplexClaimQuery intent');

  if (roleContext === 'visitor') {
    return "Claim information is only available to customers and staff.";
  }

  const policyNumber = parameters['policy-number'] || extractPolicyNumber(queryText);

  if (!policyNumber) {
    return 'Please provide the policy number for the claim you\'re asking about.';
  }

 try {
    // Step 1: Get claim details from Azure SQL
    const claimResult = await pool.request()
      .input('policyNumber', sql.VarChar, policyNumber)
      .query('SELECT * FROM fn_GetClaimDetails(@policyNumber)');

    const claim = claimResult.recordset[0];

    if (!claim) {
      return `No claim found for policy ${policyNumber}.`;
    }

    // Step 2: Get policy terms from Flask RAG
    const ragResponse = await axios.post(`${FLASK_RAG_URL}/query`, {
      question: `What are the coverage terms for ${claim.ClaimType} claims?`,
      role: roleContext
    }, { timeout: 10000 });

    const policyTerms = ragResponse.data.answer;

      // Step 3: Synthesize with GPT-4 (if you have OpenAI integration)
    // For now, return combined information
    return `Claim Status: ${claim.Status}\n` +
           `Claim Amount: $${claim.Amount}\n` +
           `Reason: ${claim.Reason}\n\n` +
           `Policy Terms: ${policyTerms}`;

  } catch (error) {
    console.error('Complex claim query error:', error);
    throw error;
  }
}

async function handleDocumentVerification(parameters, queryText, roleContext) {
  console.log('📄 Handling DocumentVerification intent');

  if (roleContext !== 'customer') {
    return "Document verification is only available for customers.";
  }

  // This would integrate with GPT-4 Vision API
  // For now, placeholder response
  return "To verify your document, please upload it through our secure portal at https://hakikisha.com/verify";
}

async function handleClaimStatus(parameters, queryText, roleContext) {
  console.log('📊 Handling ClaimStatus intent');

  if (roleContext === 'visitor') {
    return "Claim status is only available to customers and staff.";
  }

  const claimNumber = parameters['claim-number'] || parameters['claimNumber'];

  if (!claimNumber) {
    return 'Please provide your claim number (e.g., CLM123456).';
  }

  try {
    const result = await pool.request()
      .input('claimNumber', sql.VarChar, claimNumber)
      .query('SELECT * FROM fn_GetClaimStatus(@claimNumber)');

    const claim = result.recordset[0];

    if (!claim) {
      return `No claim found with number ${claimNumber}.`;
    }

    return `Your claim ${claimNumber} is currently ${claim.Status}. ` +
           `Submitted on: ${claim.SubmissionDate}. ` +
           `${claim.Status === 'Pending' ? 'We are reviewing your claim and will update you soon.' : ''}`;

  } catch (error) {
    console.error('Claim status error:', error);
    throw error;
  }
}


// ============================================
// UTILITY FUNCTIONS
// ============================================

function extractPolicyNumber(text) {
  // Try to extract policy number from text using regex
  const match = text.match(/POL\d+|[A-Z]{2,3}\d+|\b[A-Z]+\d+\b/i);
  return match ? match[0].toUpperCase() : null;
}




// Example: CustomerAuth sync endpoint
app.post('/api/customer-auth', async (req, res) => {
  const { firebase_uid, email, phone } = req.body;

  try {
    // Connect to Azure SQL

    // Check if user exists by Firebase UID
    const result = await pool.request()
      .query`SELECT * FROM CustomerAuth WHERE AuthID = ${firebase_uid}`;

    if (result.recordset.length === 0) {
      // Insert new user
      await pool.request().query`
        INSERT INTO CustomerAuth (AuthID, Email, Phone, CreatedDate)
        VALUES (${firebase_uid}, ${email}, ${phone}, GETDATE())
      `;
    }

    // Fetch the user record
    const user = await pool.request()
      .query`SELECT * FROM CustomerAuth WHERE AuthID = ${firebase_uid}`;

    res.json({ success: true, user: user.recordset[0] });
  } catch (err) {
    console.error("❌ SQL error:", err);
    res.status(500).json({ success: false, error: err.message });
  }
});





// Link to Azure SQL
app.post('/api/customer-auth', async (req, res) => {
   try {
    const { idToken } = req.body;

     // ADDED: Validation check
    if (!idToken) {
      return res.status(400).json({ 
        success: false, 
        error: 'ID token is required' 
      });
    }
    // This verifies BOTH phone and email tokens!
    const decodedToken = await admin.auth().verifyIdToken(idToken);
    const firebase_uid = decodedToken.uid;
 // const { idToken, email, phone } = req.body;
  //const firebase_uid = await verifyFirebaseToken(idToken);


   // UPDATED: Extract email and phone (one or both may be present depending on auth method)
    const email = decodedToken.email || null;  // Present for email auth
    const phone = decodedToken.phone_number || null;  // Present for phone auth

    // ADDED: Determine authentication method used
    const auth_method = phone ? 'phone' : (email ? 'email' : 'unknown');

    
    // ADDED: Log for debugging - shows which method was used
    console.log('✅ Token verified for user:', firebase_uid);
    console.log('📱 Auth method:', auth_method);
    console.log('📧 Email:', email || 'Not provided');
    console.log('📞 Phone:', phone || 'Not provided');


    // ADDED: Validation - ensure at least one contact method exists
    if (!email && !phone) {
      return res.status(400).json({
        success: false,
        error: 'User must have either email or phone number'
      });
    }


 // FIXED: Proper SQL parameter binding using mssql library
    // UPDATED: Now handles both email and phone (one or both may be null)
    const query = `
      MERGE CustomerAuth AS target
      USING (SELECT @firebase_uid AS AuthID, @email AS Email, @phone AS Phone, @auth_method AS AuthMethod) AS source
      ON target.AuthID = source.AuthID
      WHEN MATCHED THEN 
        UPDATE SET 
          Email = COALESCE(source.Email, target.Email),
          Phone = COALESCE(source.Phone, target.Phone),
          AuthMethod = source.AuthMethod,
          LastLogin = GETDATE()
      WHEN NOT MATCHED THEN 
        INSERT (AuthID, Email, Phone, CreatedDate) 
        VALUES (source.AuthID, source.Email, source.Phone, GETDATE());
    `;

  
  // FIXED: Use named parameters with pool.request()
    // UPDATED: Added auth_method parameter
    await pool.request()
      .input('firebase_uid', sql.VarChar, firebase_uid)
      .input('email', sql.VarChar, email)
      .input('phone', sql.VarChar, phone)
      .input('auth_method', sql.VarChar, auth_method)
      .query(query);

      
    // ADDED: Fetch the user record to return to frontend
    const userResult = await pool.request()
      .input('firebase_uid', sql.VarChar, firebase_uid)
      .query`SELECT * FROM CustomerAuth WHERE AuthID = @firebase_uid`;

       // ADDED: Success response with user data and auth method info
    res.json({ 
      success: true,
      message: 'User authenticated and linked successfully',
      auth_method: auth_method,  // Tell frontend which method was used
      user: userResult.recordset[0]
    });

    } catch (error) {
    // ADDED: Comprehensive error handling
    console.error('❌ Authentication error:', error);

    // Handle specific Firebase token errors
    if (error.code === 'auth/id-token-expired') {
      return res.status(401).json({ 
        success: false, 
        error: 'Token expired. Please sign in again.' 
      });
    }

    if (error.code === 'auth/argument-error') {
      return res.status(401).json({ 
        success: false, 
        error: 'Invalid token format.' 
      });
    }

    // Handle SQL errors
    if (error.number) {  // SQL Server error
      console.error('SQL Error Number:', error.number);
      return res.status(500).json({ 
        success: false, 
        error: 'Database error occurred.' 
      });
    }

    // Generic error response
    res.status(500).json({ 
      success: false, 
      error: 'Authentication failed. Please try again.' 
    });
  }
});

// OPTIONAL: Add a middleware version for protecting routes
// UPDATED: Works with both phone and email authentication
async function verifyFirebaseMiddleware(req, res, next) {
  try {
    const authHeader = req.headers.authorization;
    
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      return res.status(401).json({ error: 'No token provided' });
    }

    const idToken = authHeader.split('Bearer ')[1];
    const decodedToken = await admin.auth().verifyIdToken(idToken);
    
    // UPDATED: Attach user info to request object (works for both auth methods)
    req.firebase_uid = decodedToken.uid;
    req.user_email = decodedToken.email || null;
    req.user_phone = decodedToken.phone_number || null;
    req.auth_method = decodedToken.phone_number ? 'phone' : 'email';
    
    next();
  } catch (error) {
    console.error('❌ Token verification failed:', error);
    return res.status(401).json({ error: 'Invalid or expired token' });
  }
}

// FIXED: Example protected route using middleware
// UPDATED: Shows both email and phone if available
app.get("/api/protected", verifyFirebaseMiddleware, (req, res) => {
  res.json({ 
    message: `Welcome user ${req.firebase_uid}`,
    email: req.user_email,
    phone: req.user_phone,
    auth_method: req.auth_method
  });
});

app.get("/api/customer-profile", verifyFirebaseMiddleware, async (req, res) => {
  try {
    const result = await pool.request()
      .input('firebase_uid', sql.VarChar, req.firebase_uid)
      .query`SELECT * FROM CustomerAuth WHERE AuthID = @firebase_uid`;
    
    if (result.recordset.length === 0) {
      return res.status(404).json({ 
        success: false, 
        error: 'User profile not found' 
      });
    }

    res.json({ 
      success: true, 
      profile: result.recordset[0] 
    });
  } catch (error) {
    console.error('❌ Error fetching profile:', error);
    res.status(500).json({ 
      success: false, 
      error: 'Failed to fetch profile' 
    });
  }
});


// Example endpoint for staff auth
app.post('/api/user-auth', async (req, res) => {
  // Your logic here
  res.json({ success: true, message: "User auth endpoint hit!" });
});




// Root endpoint for testing
app.get('/', (req, res) => {
  res.send('Backend is running!');
});

// Listen on the correct port
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`Server running on port ${PORT}`));
console.log(`📍 Chat endpoint: http://localhost:${PORT}/chat`);
console.log(`📍 Webhook endpoint: http://localhost:${PORT}/webhook`);