# Neo4j Aura Permissions Fix

## Problem

You're getting this error:
```
ACCESS on database 'neo4j' is not allowed for user 'neo4j' with roles [PUBLIC, console_admin_free_ad5b837e]
```

## Solutions

### Option 1: Use a Different Database Name (Recommended)

Neo4j Aura free tier sometimes restricts access to the default 'neo4j' database. Try using a different database name:

1. In Neo4j Aura Dashboard:
   - Go to your instance
   - Create a new database (or use an existing one)
   - Note the database name (might be something like `neo4j` or `graph`)

2. Update your `.env` file:
```env
NEO4J_DATABASE=neo4j  # Try: neo4j, graph, or check your Aura dashboard
```

### Option 2: Grant Permissions

In Neo4j Browser (http://your-instance.databases.neo4j.io):

```cypher
// Grant write access (if you have admin rights)
GRANT WRITE ON DATABASE neo4j TO neo4j;
```

### Option 3: Use Default Database

If you're on Neo4j Aura free tier, try:
- Leave `NEO4J_DATABASE` empty or set to empty string
- The driver will use the default database

### Option 4: Check Your Aura Plan

- Free tier might have restrictions
- Check your Neo4j Aura dashboard for database access permissions
- You might need to upgrade or use a different database

## What I Changed

1. **Fixed Constraint**: Changed from `name IS UNIQUE` to `(name, user_id) IS UNIQUE`
   - This allows multiple users to have entities with the same name
   - Each user's data is isolated

2. **Better Error Handling**: Constraints/indexes are now optional
   - App will work even if constraints can't be created
   - You'll see warnings but the app continues

3. **Graceful Degradation**: If permissions fail, the app still tries to work

## Test After Fix

1. Restart Flask app
2. Try demo again
3. Check terminal for any warnings
4. If it still fails, check Neo4j Aura dashboard for database name

## Quick Check

Run this in Neo4j Browser to see available databases:
```cypher
SHOW DATABASES;
```

Use the database name from that list in your `.env` file.

