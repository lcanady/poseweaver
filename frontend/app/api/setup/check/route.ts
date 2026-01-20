import { NextResponse } from 'next/server';
import { adminDb } from '@/lib/firebase/admin';

export const dynamic = 'force-dynamic';

export async function GET() {
    try {
        // Check if any user with role 'admin' exists in Firestore
        const snapshot = await adminDb.collection('users')
            .where('role', '==', 'admin')
            .limit(1)
            .get();

        const adminExists = !snapshot.empty;

        return NextResponse.json({
            needs_setup: !adminExists,
            message: adminExists ? 'Setup complete' : 'Setup required'
        });
    } catch (error) {
        console.error('Error checking setup status:', error);
        // Fail safe: If DB check fails, assume setup might be needed or return error to avoid infinite loops if DB is down.
        // But returning true might lock out users if DB is just flaky.
        // Let's return error so frontend handles it.
        return NextResponse.json({
            error: 'Failed to check setup status',
            needs_setup: true // Default to true if uncertain, but frontend should handle error
        }, { status: 500 });
    }
}
