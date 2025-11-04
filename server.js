require('dotenv').config(); // Load .env variables




const express = require('express');
const app = express();
app.use(express.json());


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

// Webhook endpoint for Dialogflow
//app.post('/webhook', async (req, res) => {
  //const intent = req.body.queryResult.intent.displayName;
  //const parameters = req.body.queryResult.parameters;

  //console.log('Parameters received:', parameters);

  //console.log('Intent received:', intent);


  //try {
    // Connect to SQL (use a pool for production)
    //await sql.connect(config);

    //if (intent === 'PolicyDetails') {
      //const policyNumber = parameters['policy-number'];
      //const result = await sql.query`SELECT * FROM fn_GetPolicyDetails(${policyNumber})`;
      //const policy = result.recordset[0];

      //if (!policy) {
        //return res.json({ fulfillmentText: 'No policy found with that number.' });
      //}

      //const responseText = `Your policy ${policy.PolicyName} covers ${policy.PolicyType} and is valid until ${policy.EndDate}.`;
      //return res.json({ fulfillmentText: responseText });
    //} else {
      //return res.json({ fulfillmentText: 'Intent not recognized.' });
    //}
  //} catch (err) {
    //console.error('Error:', err);
    //return res.json({ fulfillmentText: 'Sorry, I couldn’t process your request right now.' });
  //}
//});

//const PORT = process.env.PORT;



//app.listen(PORT, () => console.log(`🚀 Server running on port ${PORT}`));





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

  if (!req.body.queryResult.intent) {
    console.log('ERROR: Missing intent in queryResult');
    return res.json({ fulfillmentText: 'No intent found in request.' });
  }

  const intent = req.body.queryResult.intent.displayName;
  const parameters = req.body.queryResult.parameters;
  
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

   
    // Use exact string comparison and also check for variations
    console.log('Comparing intent:', `"${intent}" === "PolicyDetails"`);
    
    // Try multiple intent name variations
    const intentVariations = [
      'PolicyDetails',
      'Policy Details', 
      'policydetails',
      'policy.details',
      'policy-details',
      intent.toLowerCase(),
      intent.trim()
    ];
    
    const matchedIntent = intentVariations.find(variation => 
      intent === variation || intent.toLowerCase() === variation.toLowerCase()
    );
    
    if (matchedIntent || intent.toLowerCase().includes('policy')) {
      console.log('Policy intent matched! Matched with:', matchedIntent || intent);
      
      // Try different parameter name variations
      const policyNumber = parameters['policy-number'] || 
                           parameters['policyNumber'] || 
                           parameters.number ||
                           parameters.any ||
                           parameters['policy_number'];
      
      console.log('All parameters:', Object.keys(parameters));
      console.log('Policy number extracted:', policyNumber);
      
      if (!policyNumber) {
        console.log('ERROR: No policy number found in parameters');
        console.log('Available parameter keys:', Object.keys(parameters));
        
        // Check if we can extract from the original query text
        const queryText = req.body.queryResult.queryText;
        console.log('Original query:', queryText);
        
        // Try to extract policy number from query text using regex
        const policyMatch = queryText.match(/POL\d+|[A-Z]{2,3}\d+|\b[A-Z]+\d+\b/i);
        if (policyMatch) {
          const extractedPolicy = policyMatch[0];
          console.log('Extracted policy from query text:', extractedPolicy);
          // Use the extracted policy number
         const result = await pool.request()
  .input('policyNumber', sql.VarChar, extractedPolicy)
  .query('SELECT * FROM fn_GetPolicyDetails(@policyNumber)');
          const policy = result.recordset[0];
          
          if (!policy) {
            return res.json({ 
              fulfillmentText: `No policy found with number ${extractedPolicy}.` 
            });
          }
          
          const responseText = `Your policy ${policy.PolicyName} covers ${policy.PolicyType} and is valid until ${policy.EndDate}.`;
          return res.json({ fulfillmentText: responseText });
        }
        
        return res.json({ 
          fulfillmentText: 'Please provide a valid policy number (e.g., POL123456).' 
        });
      }
      
      const result = await pool.request()
  .input('policyNumber', sql.VarChar, policyNumber)
  .query('SELECT * FROM fn_GetPolicyDetails(@policyNumber)');
      const policy = result.recordset[0];
      
      if (!policy) {
        console.log('No policy found for number:', policyNumber);
        return res.json({ 
          fulfillmentText: 'No policy found with that number.' 
        });
      }
      
      const responseText = `Your policy ${policy.PolicyName} covers ${policy.PolicyType} and is valid until ${policy.EndDate}.`;
      console.log('Sending response:', responseText);
      return res.json({ fulfillmentText: responseText });
      
    } else {
      // List all possible intents we're receiving to help debug
      console.log('Intent not recognized. Received intent:', intent);
      console.log('Expected variations: PolicyDetails, Policy Details, etc.');
      console.log('Character codes for received intent:', 
        intent.split('').map(char => char.charCodeAt(0)));
      
      return res.json({ 
        fulfillmentText: `Intent "${intent}" not recognized. Please check your Dialogflow intent configuration.` 
      });
    }
  } catch (err) {
    console.error('Database/Server Error:', err);
    return res.json({ 
      fulfillmentText: 'Sorry, I couldn\'t process your request right now.' 
    });
  }
});



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