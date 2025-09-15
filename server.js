require('dotenv').config(); // Load .env variables

const express = require('express');
const app = express(); // This line was missing!

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
    encrypt: true,
    trustServerCertificate: false
  }
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

// Add CORS headers for Dialogflow
app.use((req, res, next) => {
  res.header('Access-Control-Allow-Origin', '*');
  res.header('Access-Control-Allow-Headers', 'Origin, X-Requested-With, Content-Type, Accept');
  next();
});

// Test endpoint to verify webhook is accessible
app.get('/webhook', (req, res) => {
  console.log('GET request to /webhook - webhook is accessible');
  res.json({ 
    status: 'Webhook is working',
    timestamp: new Date().toISOString(),
    message: 'This endpoint receives POST requests from Dialogflow'
  });
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
    await sql.connect(config);
    
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
          const result = await sql.query`SELECT * FROM fn_GetPolicyDetails(${extractedPolicy})`;
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
      
      const result = await sql.query`SELECT * FROM fn_GetPolicyDetails(${policyNumber})`;
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
    // Check if user exists by Firebase UID
    const result = await sql.query`SELECT * FROM CustomerAuth WHERE AuthID = ${firebase_uid}`;
    if (result.recordset.length === 0) {
      // Insert new user (fill in other fields as needed)
      await sql.query`
        INSERT INTO CustomerAuth (AuthID, Email, Phone, CreatedDate)
        VALUES (${firebase_uid}, ${email}, ${phone}, GETDATE())
      `;
    }
    // Optionally, fetch and return user info
    const user = await sql.query`SELECT * FROM CustomerAuth WHERE AuthID = ${firebase_uid}`;
    res.json({ success: true, user: user.recordset[0] });
  } catch (err) {
    res.status(500).json({ success: false, error: err.message });
  }
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`🚀 Server running on port ${PORT}`));