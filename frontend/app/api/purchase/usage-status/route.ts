
import { NextResponse } from 'next/server';
import { adminDb } from '@/lib/firebase/admin';
import { FirestoreUser } from '@/lib/types/firestore-schema';

export const dynamic = 'force-dynamic';

export async function GET(request: Request) {
    try {
        const { searchParams } = new URL(request.url);
        const userId = searchParams.get('user_id');

        if (!userId) {
            return NextResponse.json({ error: 'User ID is required' }, { status: 400 });
        }

        const userDoc = await adminDb.collection('users').doc(userId).get();

        if (!userDoc.exists) {
            // Default to free if user doc doesn't exist yet
            return NextResponse.json({
                success: true,
                usage_info: {
                    plan: 'free',
                    credits: { total: 10, used: 0, remaining: 10 },
                    character_count: 0,
                    character_limit: 5,
                    subscription_status: 'free'
                }
            });
        }

        const userData = userDoc.data() as FirestoreUser;

        // Map subscriptionStatus to plan for the frontend
        const isAdmin = userData.role === 'admin' || userData.subscriptionStatus === 'admin';
        const plan = userData.subscriptionStatus || 'free';
        
        return NextResponse.json({
            success: true,
            usage_info: {
                plan: plan,
                credits: {
                    total: isAdmin ? 1000 : 10,
                    used: userData.poseGenerationsUsed || 0,
                    remaining: isAdmin ? 1000 - (userData.poseGenerationsUsed || 0) : 10 - (userData.poseGenerationsUsed || 0)
                },
                character_count: 0,
                character_limit: isAdmin ? 100 : 5,
                subscription_status: plan // Using plan name for badge logic in dashboard
            }
        });

    } catch (error: any) {
        console.error('Error fetching usage status:', error);
        return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
    }
}
