import { Character } from "@/hooks/useCharacter";

interface CharacterMetadataProps {
  character: Character;
}

interface MetadataSectionProps {
  title: string;
  content: string | string[];
  type?: 'text' | 'list';
}

function MetadataSection({ title, content, type = 'text' }: MetadataSectionProps) {
  if (!content || (Array.isArray(content) && content.length === 0)) {
    return null;
  }

  return (
    <div>
      <h3 className="text-lg font-semibold mb-2">{title}</h3>
      {type === 'list' && Array.isArray(content) ? (
        <ul className="list-disc pl-5 space-y-1">
          {content.map((item: string, index: number) => (
            <li key={index}>{item}</li>
          ))}
        </ul>
      ) : (
        <p className="whitespace-pre-wrap">{content as string}</p>
      )}
    </div>
  );
}

export function CharacterMetadata({ character }: CharacterMetadataProps) {
  const { metadata } = character;

  return (
    <div className="space-y-6">
      <MetadataSection 
        title="Description" 
        content={character.description} 
      />
      
      {metadata && (
        <>
          <MetadataSection 
            title="Background" 
            content={metadata.background || ''} 
          />
          
          <MetadataSection 
            title="Personality" 
            content={metadata.personality || []} 
            type="list" 
          />
          
          <MetadataSection 
            title="Skills" 
            content={metadata.skills || []} 
            type="list" 
          />
          
          <MetadataSection 
            title="Goals" 
            content={metadata.goals || []} 
            type="list" 
          />
          
          <MetadataSection 
            title="Voice Notes" 
            content={metadata.voice_notes || ''} 
          />
        </>
      )}
    </div>
  );
}