import { NextResponse } from 'next/server';

export const dynamic = 'force-dynamic';

export async function GET() {
    // Mock unread count
    return NextResponse.json({
        success: true,
        unread_count: 0
    });
}
