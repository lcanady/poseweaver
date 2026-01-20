import { NextResponse } from 'next/server';
import { adminAuth, adminDb } from '@/lib/firebase/admin';

export async function POST(request: Request) {
    try {
        const { email, password, display_name, idToken } = await request.json();

        if (idToken) {
            // Handle Google Signup (Promotion to Admin)
            try {
                const decodedToken = await adminAuth.verifyIdToken(idToken);
                const uid = decodedToken.uid;

                // Set Custom Claims for Admin
                await adminAuth.setCustomUserClaims(uid, {
                    admin: true,
                    superuser: true
                });

                // Create User Document in Firestore
                await adminDb.collection('users').doc(uid).set({
                    email: decodedToken.email,
                    displayName: display_name || decodedToken.name || 'Admin User',
                    photoURL: decodedToken.picture || null,
                    role: 'admin',
                    subscriptionStatus: 'admin',
                    isActive: true,
                    poseGenerationsUsed: 0,
                    extraPoseGenerations: 0,
                    createdAt: new Date(),
                    updatedAt: new Date(),
                }, { merge: true }); // Merge in case doc exists

                return NextResponse.json({
                    success: true,
                    userId: uid,
                    message: 'Admin account created successfully via Google'
                });

            } catch (error: any) {
                console.error('Error verifying Google token:', error);
                return NextResponse.json(
                    { error: 'Invalid Google token' },
                    { status: 401 }
                );
            }
        }

        // Handle Email/Password Signup
        if (!email || !password || !display_name) {
            return NextResponse.json(
                { error: 'Email, password, and display name are required' },
                { status: 400 }
            );
        }

        // Create Firebase User
        try {
            const userRecord = await adminAuth.createUser({
                email,
                password,
                displayName: display_name,
                // emailVerified: true, // Optional: might want verification
            });

            // Set Custom Claims for Admin
            await adminAuth.setCustomUserClaims(userRecord.uid, {
                admin: true,
                superuser: true
            });

            // Create User Document in Firestore
            await adminDb.collection('users').doc(userRecord.uid).set({
                email: userRecord.email,
                displayName: display_name,
                role: 'admin',
                subscriptionStatus: 'admin',
                isActive: true,
                poseGenerationsUsed: 0,
                extraPoseGenerations: 0,
                createdAt: new Date(),
                updatedAt: new Date(),
            });

            return NextResponse.json({
                success: true,
                userId: userRecord.uid,
                message: 'Admin account created successfully'
            });

        } catch (error: any) {
            console.error('Error creating user:', error);
            return NextResponse.json(
                { error: error.message || 'Failed to create user' },
                { status: 500 }
            );
        }

    } catch (error) {
        console.error('Error in create-admin endpoint:', error);
        return NextResponse.json(
            { error: 'Internal Server Error' },
            { status: 500 }
        );
    }
}
