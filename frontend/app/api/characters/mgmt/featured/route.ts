import { NextResponse } from 'next/server';

export const dynamic = 'force-dynamic';

export async function GET() {
    // Mock featured characters
    const featuredCharacters = [
        {
            _id: '1',
            name: 'Elara Moonwhisper',
            description: 'A nimble elven rogue with a penchant for ancient artifacts and shadow magic.',
            profile_image: 'https://images.unsplash.com/photo-1544005313-94ddf0286df2?auto=format&fit=crop&q=80&w=400&h=400',
            tags: ['Elf', 'Rogue', 'Magic']
        },
        {
            _id: '2',
            name: 'Thorne Ironbreaker',
            description: 'A dwarven paladin sworn to protect the mountain kingdoms from deep underground threats.',
            profile_image: 'https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?auto=format&fit=crop&q=80&w=400&h=400',
            tags: ['Dwarf', 'Paladin', 'Tank']
        },
        {
            _id: '3',
            name: 'Zephyr Stormcaller',
            description: 'A chaotic air genasi sorcerer who channels the power of the storms.',
            profile_image: 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?auto=format&fit=crop&q=80&w=400&h=400',
            tags: ['Genasi', 'Sorcerer', 'Storm']
        }
    ];

    return NextResponse.json({
        success: true,
        data: featuredCharacters,
        meta: {
            total: featuredCharacters.length,
            limit: 12
        }
    });
}
