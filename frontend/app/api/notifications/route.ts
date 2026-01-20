import { NextResponse } from 'next/server';

export const dynamic = 'force-dynamic';

export async function GET() {
    // Mock empty notifications list for now
    return NextResponse.json({
        success: true,
        notifications: [],
        unread_count: 0
    });
}
