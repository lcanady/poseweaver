"use client"

import { useState, useEffect } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { ChevronLeft, ChevronRight, User, Sparkles } from "lucide-react"
import { cn } from "@/lib/utils"

interface FeaturedCharacter {
  _id: string
  name: string
  description: string
  profile_image: string
  tags?: string[]
  created_at?: string
}

interface FeaturedCharactersResponse {
  success: boolean
  data: FeaturedCharacter[]
  meta: {
    total: number
    limit: number
  }
}

export function FeaturedCharacters() {
  const [characters, setCharacters] = useState<FeaturedCharacter[]>([])
  const [currentIndex, setCurrentIndex] = useState(0)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Number of characters to show at once (responsive)
  const [itemsPerView, setItemsPerView] = useState(3)

  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth < 768) {
        setItemsPerView(1) // Mobile: 1 character
      } else if (window.innerWidth < 1024) {
        setItemsPerView(2) // Tablet: 2 characters
      } else {
        setItemsPerView(3) // Desktop: 3 characters
      }
    }

    handleResize()
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [])

  useEffect(() => {
    fetchFeaturedCharacters()
  }, [])

  const fetchFeaturedCharacters = async () => {
    try {
      setIsLoading(true)
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5001'}/api/characters/mgmt/featured?limit=12`
      )
      
      if (!response.ok) {
        throw new Error('Failed to fetch featured characters')
      }

      const data: FeaturedCharactersResponse = await response.json()
      
      if (data.success && data.data.length > 0) {
        setCharacters(data.data)
        setError(null)
      } else {
        setError('No featured characters available')
      }
    } catch (err) {
      console.error('Error fetching featured characters:', err)
      setError('Unable to load featured characters')
    } finally {
      setIsLoading(false)
    }
  }

  const nextSlide = () => {
    setCurrentIndex((prev) => {
      const maxIndex = Math.max(0, characters.length - itemsPerView)
      return prev >= maxIndex ? 0 : prev + 1
    })
  }

  const prevSlide = () => {
    setCurrentIndex((prev) => {
      const maxIndex = Math.max(0, characters.length - itemsPerView)
      return prev <= 0 ? maxIndex : prev - 1
    })
  }

  const goToSlide = (index: number) => {
    const maxIndex = Math.max(0, characters.length - itemsPerView)
    setCurrentIndex(Math.min(index, maxIndex))
  }

  if (isLoading) {
    return (
      <section className="py-16 bg-muted/30">
        <div className="container mx-auto px-4">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold mb-4">Featured Characters</h2>
            <p className="text-muted-foreground max-w-2xl mx-auto">
              Discover amazing characters created by our community
            </p>
          </div>
          <div className="flex justify-center items-center h-64">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          </div>
        </div>
      </section>
    )
  }

  if (error || characters.length === 0) {
    return (
      <section className="py-16 bg-muted/30">
        <div className="container mx-auto px-4">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold mb-4">Featured Characters</h2>
            <p className="text-muted-foreground max-w-2xl mx-auto">
              Discover amazing characters created by our community
            </p>
          </div>
          <div className="text-center py-12">
            <User className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
            <p className="text-muted-foreground">
              {error || 'No featured characters available at the moment'}
            </p>
          </div>
        </div>
      </section>
    )
  }

  const maxIndex = Math.max(0, characters.length - itemsPerView)
  const visibleCharacters = characters.slice(currentIndex, currentIndex + itemsPerView)

  return (
    <section className="py-16 bg-muted/30">
      <div className="container mx-auto px-4">
        {/* Header */}
        <div className="text-center mb-12">
          <div className="flex items-center justify-center gap-2 mb-4">
            <Sparkles className="h-6 w-6 text-primary" />
            <h2 className="text-3xl font-bold">Featured Characters</h2>
          </div>
          <p className="text-muted-foreground max-w-2xl mx-auto">
            Discover amazing characters created by our community. Get inspired for your next roleplay adventure!
          </p>
        </div>

        {/* Carousel */}
        <div className="relative">
          {/* Navigation Buttons */}
          {characters.length > itemsPerView && (
            <>
              <Button
                variant="outline"
                size="icon"
                className="absolute left-0 top-1/2 -translate-y-1/2 z-10 bg-background/80 backdrop-blur-sm"
                onClick={prevSlide}
                disabled={currentIndex === 0}
              >
                <ChevronLeft className="h-4 w-4" />
              </Button>
              <Button
                variant="outline"
                size="icon"
                className="absolute right-0 top-1/2 -translate-y-1/2 z-10 bg-background/80 backdrop-blur-sm"
                onClick={nextSlide}
                disabled={currentIndex >= maxIndex}
              >
                <ChevronRight className="h-4 w-4" />
              </Button>
            </>
          )}

          {/* Character Cards */}
          <div className="mx-8">
            <div className={cn(
              "grid gap-6",
              itemsPerView === 1 && "grid-cols-1",
              itemsPerView === 2 && "grid-cols-2",
              itemsPerView === 3 && "grid-cols-3"
            )}>
              {visibleCharacters.map((character) => (
                <Card key={character._id} className="overflow-hidden hover:shadow-lg transition-shadow">
                  <div className="aspect-square relative overflow-hidden">
                    <img
                      src={character.profile_image}
                      alt={character.name}
                      className="w-full h-full object-cover transition-transform hover:scale-105"
                      onError={(e) => {
                        const target = e.target as HTMLImageElement
                        target.src = `https://ui-avatars.com/api/?name=${encodeURIComponent(character.name)}&background=random&color=fff&size=400`
                      }}
                    />
                  </div>
                  <CardContent className="p-6">
                    <h3 className="font-semibold text-lg mb-2">{character.name}</h3>
                    <p className="text-muted-foreground text-sm line-clamp-3 mb-4">
                      {character.description}
                    </p>
                    {character.tags && character.tags.length > 0 && (
                      <div className="flex flex-wrap gap-1">
                        {character.tags.slice(0, 3).map((tag, index) => (
                          <span
                            key={index}
                            className="inline-block bg-primary/10 text-primary text-xs px-2 py-1 rounded-full"
                          >
                            {tag}
                          </span>
                        ))}
                        {character.tags.length > 3 && (
                          <span className="inline-block bg-muted text-muted-foreground text-xs px-2 py-1 rounded-full">
                            +{character.tags.length - 3}
                          </span>
                        )}
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>

          {/* Dots Indicator */}
          {characters.length > itemsPerView && (
            <div className="flex justify-center mt-8 gap-2">
              {Array.from({ length: maxIndex + 1 }).map((_, index) => (
                <button
                  key={index}
                  className={cn(
                    "w-2 h-2 rounded-full transition-colors",
                    index === currentIndex
                      ? "bg-primary"
                      : "bg-muted-foreground/30 hover:bg-muted-foreground/50"
                  )}
                  onClick={() => goToSlide(index)}
                />
              ))}
            </div>
          )}
        </div>

        {/* Call to Action */}
        <div className="text-center mt-12">
          <p className="text-muted-foreground mb-4">
            Ready to create your own character?
          </p>
          <Button asChild>
            <a href="/auth/register">Get Started Free</a>
          </Button>
        </div>
      </div>
    </section>
  )
}
