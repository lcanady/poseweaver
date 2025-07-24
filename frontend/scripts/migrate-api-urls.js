#!/usr/bin/env node

/**
 * Script to migrate hardcoded API URLs to use dynamic getApiUrl() function
 * This will update all files that use the old pattern:
 * ${getApiUrl()}
 * to use: ${getApiUrl()}
 */

const fs = require('fs');
const path = require('path');

const FRONTEND_DIR = path.join(__dirname, '..');
const EXTENSIONS = ['.ts', '.tsx', '.js', '.jsx'];

// Pattern to match the old API URL usage
const OLD_PATTERN = /\$\{process\.env\.NEXT_PUBLIC_API_URL \|\| ['"`]http:\/\/localhost:5001['"`]\}/g;
const NEW_PATTERN = '${getApiUrl()}';

// Import statement to add if not present
const IMPORT_STATEMENT = "import { getApiUrl } from '@/utils/api-utils';";

function findFilesWithExtensions(dir, extensions) {
  const files = [];
  
  function traverse(currentDir) {
    const items = fs.readdirSync(currentDir);
    
    for (const item of items) {
      const fullPath = path.join(currentDir, item);
      const stat = fs.statSync(fullPath);
      
      if (stat.isDirectory() && !item.startsWith('.') && item !== 'node_modules') {
        traverse(fullPath);
      } else if (stat.isFile() && extensions.some(ext => item.endsWith(ext))) {
        files.push(fullPath);
      }
    }
  }
  
  traverse(dir);
  return files;
}

function hasImport(content, importStatement) {
  return content.includes("from '@/utils/api-utils'");
}

function addImport(content, importStatement) {
  // Find the last import statement
  const lines = content.split('\n');
  let lastImportIndex = -1;
  
  for (let i = 0; i < lines.length; i++) {
    if (lines[i].trim().startsWith('import ') && lines[i].includes('from ')) {
      lastImportIndex = i;
    }
  }
  
  if (lastImportIndex >= 0) {
    lines.splice(lastImportIndex + 1, 0, importStatement);
  } else {
    // No imports found, add at the top after 'use client' if present
    let insertIndex = 0;
    if (lines[0] && lines[0].includes('use client')) {
      insertIndex = 1;
      if (lines[1] === '') insertIndex = 2; // Skip empty line after 'use client'
    }
    lines.splice(insertIndex, 0, importStatement, '');
  }
  
  return lines.join('\n');
}

function migrateFile(filePath) {
  const content = fs.readFileSync(filePath, 'utf8');
  
  // Check if file contains the old pattern
  if (!OLD_PATTERN.test(content)) {
    return false; // No changes needed
  }
  
  let newContent = content;
  
  // Replace the old pattern with new pattern
  newContent = newContent.replace(OLD_PATTERN, NEW_PATTERN);
  
  // Add import if not present
  if (!hasImport(newContent, IMPORT_STATEMENT)) {
    newContent = addImport(newContent, IMPORT_STATEMENT);
  }
  
  // Write back to file
  fs.writeFileSync(filePath, newContent, 'utf8');
  return true;
}

function main() {
  console.log('🔍 Finding TypeScript/JavaScript files...');
  const files = findFilesWithExtensions(FRONTEND_DIR, EXTENSIONS);
  
  console.log(`📁 Found ${files.length} files to check`);
  
  let migratedCount = 0;
  const migratedFiles = [];
  
  for (const file of files) {
    const relativePath = path.relative(FRONTEND_DIR, file);
    
    try {
      if (migrateFile(file)) {
        migratedCount++;
        migratedFiles.push(relativePath);
        console.log(`✅ Migrated: ${relativePath}`);
      }
    } catch (error) {
      console.error(`❌ Error migrating ${relativePath}:`, error.message);
    }
  }
  
  console.log(`\n🎉 Migration complete!`);
  console.log(`📊 Migrated ${migratedCount} files`);
  
  if (migratedFiles.length > 0) {
    console.log('\n📝 Files that were updated:');
    migratedFiles.forEach(file => console.log(`   - ${file}`));
  }
  
  console.log('\n🔧 Next steps:');
  console.log('1. Review the changes to ensure they look correct');
  console.log('2. Test the application from both localhost and network IP');
  console.log('3. Restart your backend server if needed');
}

if (require.main === module) {
  main();
}
