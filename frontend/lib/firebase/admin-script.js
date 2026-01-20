
const admin = require('firebase-admin');

// Adjust path as needed for your keys
const serviceAccount = require('./serviceAccountKey.json');

if (!admin.apps.length) {
    admin.initializeApp({
        credential: admin.credential.cert(serviceAccount)
    });
}

const adminDb = admin.firestore();
const adminAuth = admin.auth();

module.exports = { adminDb, adminAuth };
