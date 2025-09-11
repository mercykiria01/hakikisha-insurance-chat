require('dotenv').config(); // Load .env variables

const express = require('express');

const bcrypt = require('bcryptjs');

const { v4: uuidv4 } = require('uuid');

const { CosmosClient } = require('@azure/cosmos');

const bodyParser = require('body-parser');

const nodemailer = require('nodemailer');

const sql = require('mssql');



const app = express();

app.use(bodyParser.json());

app.use(bodyParser.urlencoded({ extended: true }));

app.use(express.static(__dirname));



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

app.post('/login', async (req, res) => {
  try {
    const { email, password } = req.body;
    if (!email || !password) {
      return res.status(400).json({ error: "Email and password are required" });
    }

    const result = await sql.query`SELECT * FROM Users WHERE email = ${email}`;
    const user = result.recordset[0];

    if (!user) {
      return res.status(400).json({ error: "Invalid credentials" });
    }
    if (!user.verified) {
      return res.status(403).json({ error: "Please verify your account with the OTP sent to your email." });
    }

    const isMatch = await bcrypt.compare(password, user.password);
    if (!isMatch) {
      return res.status(400).json({ error: "Invalid credentials" });
    }

    res.status(200).json({ message: "Login successful", role: user.role });
  } catch (error) {
    console.error("❌ Login error:", error);
    res.status(500).json({ error: "Server error" });
  }
});

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
app.post('/webhook', async (req, res) => {
  const intent = req.body.queryResult.intent.displayName;
  const parameters = req.body.queryResult.parameters;

  try {
    // Connect to SQL (use a pool for production)
    await sql.connect(config);

    if (intent === 'policy.details') {
      const policyNumber = parameters['policy-number'];
      const result = await sql.query`SELECT * FROM fn_GetPolicyDetails(${policyNumber})`;
      const policy = result.recordset[0];

      if (!policy) {
        return res.json({ fulfillmentText: 'No policy found with that number.' });
      }

      const responseText = `Your policy ${policy.PolicyName} covers ${policy.PolicyType} and is valid until ${policy.EndDate}.`;
      return res.json({ fulfillmentText: responseText });
    } else {
      return res.json({ fulfillmentText: 'Intent not recognized.' });
    }
  } catch (err) {
    console.error('Error:', err);
    return res.json({ fulfillmentText: 'Sorry, I couldn’t process your request right now.' });
  }
});

const PORT = process.env.PORT || 5000;

app.listen(PORT, () => console.log(`🚀 Server running on port ${PORT}`));



