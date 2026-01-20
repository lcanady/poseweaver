import { NextResponse } from 'next/server';
import { adminAuth } from '@/lib/firebase/admin';
import { dataService } from '@/lib/services/data-service';
import { headers } from 'next/headers';

export const dynamic = 'force-dynamic';

export async function GET(request: Request) {
    try {
        const headersList = await headers();
        const authorization = headersList.get('authorization');

        if (!authorization?.startsWith('Bearer ')) {
            return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
        }

        const idToken = authorization.split('Bearer ')[1];

        // Verify token
        try {
            const decodedToken = await adminAuth.verifyIdToken(idToken);
            const userId = decodedToken.uid;

            const characters = await dataService.getCharacters(userId);

            return NextResponse.json({
                success: true,
                data: characters
            });

        } catch (error) {
            console.error('Token verification failed:', error);
            return NextResponse.json({ error: 'Invalid token' }, { status: 401 });
        }

    } catch (error) {
        console.error('Error fetching characters:', error);
        return NextResponse.json(
            { error: 'Internal Server Error' },
            { status: 500 }
        );
    }
}

// Handler for creating a new character
export async function POST(request: Request) {
    try {
        const headersList = await headers();
        const authorization = headersList.get('authorization');

        if (!authorization?.startsWith('Bearer ')) {
            return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
        }

        const idToken = authorization.split('Bearer ')[1];

        // Verify token
        try {
            const decodedToken = await adminAuth.verifyIdToken(idToken);
            const userId = decodedToken.uid;

            const body = await request.json();

            // Basic validation
            if (!body.name) {
                return NextResponse.json({ error: 'Name is required' }, { status: 400 });
            }

            const charId = await dataService.createCharacter(userId, {
                ...body,
                tags: body.tags || [],
            });

            // Return the created object with ID (fetch it back or construct it)
            // Constructing it is faster
            return NextResponse.json({
                success: true,
                data: {
                    id: charId,
                    userId,
                    ...body,
                    createdAt: new Date().toISOString(),
                    updatedAt: new Date().toISOString()
                }
            });

        } catch (error) {
            console.error('Token verification failed:', error);
            return NextResponse.json({ error: 'Invalid token' }, { status: 401 });
        }
    } catch (error) {
        console.error('Error creating character:', error);
        return NextResponse.json(
            { error: 'Internal Server Error' },
            { status: 500 }
        );
    }
}
