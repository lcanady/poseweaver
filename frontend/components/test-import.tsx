// This is a test component to verify path resolution
import { cn } from '../lib';

export default function TestImport() {
  return (
    <div className={cn('p-4', 'bg-gray-100')}>
      Path resolution test component
    </div>
  );
}
