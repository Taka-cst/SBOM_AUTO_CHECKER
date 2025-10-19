-- Migration: Change SBOM ID from Integer to UUID
-- Date: 2025-10-17

BEGIN;

-- Step 1: Add new UUID column to sboms table
ALTER TABLE sboms ADD COLUMN new_id UUID DEFAULT gen_random_uuid();

-- Step 2: Update new_id with generated UUIDs
UPDATE sboms SET new_id = gen_random_uuid();

-- Step 3: Add new UUID column to scan_results table
ALTER TABLE scan_results ADD COLUMN new_sbom_id UUID;

-- Step 4: Update scan_results.new_sbom_id to match sboms.new_id
UPDATE scan_results sr
SET new_sbom_id = s.new_id
FROM sboms s
WHERE sr.sbom_id = s.id;

-- Step 5: Drop old foreign key constraints (if any)
-- ALTER TABLE scan_results DROP CONSTRAINT IF EXISTS fk_scan_results_sbom_id;

-- Step 6: Drop old columns
ALTER TABLE sboms DROP COLUMN id;
ALTER TABLE scan_results DROP COLUMN sbom_id;

-- Step 7: Rename new columns to original names
ALTER TABLE sboms RENAME COLUMN new_id TO id;
ALTER TABLE scan_results RENAME COLUMN new_sbom_id TO sbom_id;

-- Step 8: Set NOT NULL constraints
ALTER TABLE sboms ALTER COLUMN id SET NOT NULL;
ALTER TABLE scan_results ALTER COLUMN sbom_id SET NOT NULL;

-- Step 9: Add primary key constraint
ALTER TABLE sboms ADD PRIMARY KEY (id);

-- Step 10: Add index
CREATE INDEX IF NOT EXISTS ix_sboms_id ON sboms(id);
CREATE INDEX IF NOT EXISTS ix_scan_results_sbom_id ON scan_results(sbom_id);

COMMIT;
