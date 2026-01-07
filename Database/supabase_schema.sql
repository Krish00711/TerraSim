-- ============================================
-- AGRICULTURAL SIMULATION DATABASE SCHEMA
-- Supabase PostgreSQL Schema
-- ============================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- TABLE: crops
-- Stores crop profiles with environmental requirements
-- ============================================
CREATE TABLE IF NOT EXISTS crops (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) UNIQUE NOT NULL,
    category VARCHAR(50) NOT NULL, -- e.g., 'cereal', 'legume', 'vegetable', 'fruit'
    
    -- Temperature requirements (°C)
    temp_min DECIMAL(5,2) NOT NULL,
    temp_max DECIMAL(5,2) NOT NULL,
    temp_optimal DECIMAL(5,2),
    
    -- Rainfall requirements (mm/year)
    rainfall_min INTEGER NOT NULL,
    rainfall_max INTEGER NOT NULL,
    rainfall_optimal INTEGER,
    
    -- Humidity tolerance (%)
    humidity_min DECIMAL(5,2) DEFAULT 40,
    humidity_max DECIMAL(5,2) DEFAULT 90,
    humidity_tolerance DECIMAL(3,2) DEFAULT 0.7, -- 0-1 scale
    
    -- Soil requirements
    soil_ph_min DECIMAL(3,1) DEFAULT 5.5,
    soil_ph_max DECIMAL(3,1) DEFAULT 8.0,
    soil_type VARCHAR(50), -- 'loamy', 'clayey', 'sandy', 'any'
    root_depth VARCHAR(20) DEFAULT 'medium', -- 'shallow', 'medium', 'deep'
    
    -- Salt tolerance
    salt_tolerance VARCHAR(20) DEFAULT 'low', -- 'low', 'medium', 'high'
    
    -- Growth characteristics
    growing_season_days INTEGER DEFAULT 120,
    ideal_yield INTEGER NOT NULL, -- kg/hectare
    
    -- Metadata
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================
-- TABLE: terrain_modifiers
-- Environmental modifiers based on terrain type
-- ============================================
CREATE TABLE IF NOT EXISTS terrain_modifiers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    terrain_type VARCHAR(50) UNIQUE NOT NULL,
    
    -- Modifier factors (0.0 to 1.0+)
    water_retention_factor DECIMAL(3,2) NOT NULL, -- Water retention capacity
    soil_depth_factor DECIMAL(3,2) NOT NULL, -- Available soil depth
    erosion_risk DECIMAL(3,2) NOT NULL, -- 0=none, 1=severe
    drainage_quality DECIMAL(3,2) NOT NULL, -- 0=poor, 1=excellent
    
    -- Microclimate modifiers
    temp_modifier DECIMAL(4,2) DEFAULT 0.0, -- Temperature adjustment (±°C)
    wind_exposure DECIMAL(3,2) DEFAULT 0.5, -- 0=sheltered, 1=exposed
    
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================
-- TABLE: simulations
-- Stores completed simulation results
-- ============================================
CREATE TABLE IF NOT EXISTS simulations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Input parameters
    crop_name VARCHAR(100) NOT NULL,
    latitude DECIMAL(9,6) NOT NULL,
    longitude DECIMAL(9,6) NOT NULL,
    terrain VARCHAR(50) NOT NULL,
    
    -- Environmental inputs
    avg_temp DECIMAL(5,2),
    avg_rainfall INTEGER,
    humidity DECIMAL(5,2),
    wind_speed DECIMAL(5,2),
    
    -- Simulation results
    success_probability DECIMAL(5,3) NOT NULL, -- 0.000 to 1.000
    expected_yield DECIMAL(10,2) NOT NULL,
    risk_level VARCHAR(20) NOT NULL, -- 'Low', 'Medium', 'High'
    
    -- Metadata
    is_override BOOLEAN DEFAULT FALSE,
    simulation_runs INTEGER DEFAULT 10000,
    explanation TEXT,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Foreign key (optional, if you want referential integrity)
    CONSTRAINT fk_crop FOREIGN KEY (crop_name) REFERENCES crops(name) ON DELETE CASCADE
);

-- ============================================
-- TABLE: user_feedback (optional)
-- Collects user feedback on simulation accuracy
-- ============================================
CREATE TABLE IF NOT EXISTS user_feedback (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    simulation_id UUID REFERENCES simulations(id) ON DELETE CASCADE,
    
    accuracy_rating INTEGER CHECK (accuracy_rating >= 1 AND accuracy_rating <= 5),
    actual_yield DECIMAL(10,2), -- User-reported actual yield
    comments TEXT,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================
-- INDEXES for performance
-- ============================================
CREATE INDEX idx_crops_name ON crops(name);
CREATE INDEX idx_crops_category ON crops(category);
CREATE INDEX idx_simulations_crop ON simulations(crop_name);
CREATE INDEX idx_simulations_location ON simulations(latitude, longitude);
CREATE INDEX idx_simulations_created ON simulations(created_at DESC);
CREATE INDEX idx_terrain_type ON terrain_modifiers(terrain_type);

-- ============================================
-- SAMPLE DATA: Crops
-- ============================================
INSERT INTO crops (name, category, temp_min, temp_max, temp_optimal, rainfall_min, rainfall_max, rainfall_optimal, ideal_yield, growing_season_days, description) VALUES
('Rice', 'cereal', 20, 35, 28, 1000, 2500, 1500, 6000, 120, 'Water-intensive cereal crop, requires flooded conditions'),
('Wheat', 'cereal', 10, 25, 18, 400, 900, 650, 4500, 140, 'Cool-season cereal, drought-tolerant'),
('Corn (Maize)', 'cereal', 15, 35, 25, 500, 1200, 800, 7000, 110, 'Warm-season cereal, high yield potential'),
('Soybean', 'legume', 18, 30, 24, 600, 1200, 900, 3500, 100, 'Nitrogen-fixing legume, moderate water needs'),
('Cotton', 'fiber', 20, 35, 28, 600, 1500, 1000, 2000, 180, 'Warm-season fiber crop, requires long growing season'),
('Potato', 'vegetable', 10, 25, 18, 500, 1000, 750, 35000, 90, 'Cool-season tuber crop, high water sensitivity'),
('Tomato', 'vegetable', 18, 30, 24, 400, 800, 600, 50000, 80, 'Warm-season vegetable, requires consistent moisture'),
('Sugarcane', 'industrial', 20, 35, 28, 1500, 2500, 2000, 70000, 365, 'Tropical crop, very high water requirements'),
('Groundnut (Peanut)', 'legume', 20, 30, 25, 500, 1000, 750, 2500, 120, 'Warm-season legume, drought-tolerant'),
('Sunflower', 'oilseed', 15, 30, 22, 400, 800, 600, 2200, 100, 'Oilseed crop, moderate drought tolerance');

-- ============================================
-- SAMPLE DATA: Terrain Modifiers
-- ============================================
INSERT INTO terrain_modifiers (terrain_type, water_retention_factor, soil_depth_factor, erosion_risk, drainage_quality, description) VALUES
('plain', 1.0, 1.0, 0.1, 0.9, 'Flat terrain with good soil depth and minimal erosion'),
('plateau', 0.8, 0.9, 0.2, 0.85, 'Elevated flat terrain with moderate water retention'),
('mountain', 0.5, 0.6, 0.7, 0.95, 'Steep slopes with high erosion risk and shallow soil'),
('valley', 1.2, 1.1, 0.15, 0.7, 'Low-lying area with excellent water retention but potential drainage issues'),
('coastal', 0.9, 0.95, 0.3, 0.9, 'Coastal region with salt spray exposure and wind');

-- ============================================
-- VIEWS for convenience
-- ============================================

-- View: Recent high-risk simulations
CREATE OR REPLACE VIEW high_risk_simulations AS
SELECT 
    id,
    crop_name,
    latitude,
    longitude,
    success_probability,
    risk_level,
    created_at
FROM simulations
WHERE risk_level = 'High'
ORDER BY created_at DESC;

-- View: Crop success rates by terrain
CREATE OR REPLACE VIEW crop_success_by_terrain AS
SELECT 
    crop_name,
    terrain,
    AVG(success_probability) as avg_success_rate,
    AVG(expected_yield) as avg_yield,
    COUNT(*) as simulation_count
FROM simulations
GROUP BY crop_name, terrain
ORDER BY crop_name, avg_success_rate DESC;

-- ============================================
-- FUNCTIONS for data updates
-- ============================================

-- Auto-update timestamp function
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for crops table
CREATE TRIGGER update_crops_updated_at
BEFORE UPDATE ON crops
FOR EACH ROW
EXECUTE FUNCTION update_updated_at();

-- ============================================
-- ROW LEVEL SECURITY (Optional)
-- Enable if you want user-specific access control
-- ============================================

-- Enable RLS on tables
-- ALTER TABLE crops ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE simulations ENABLE ROW LEVEL SECURITY;

-- Example policy: Allow all authenticated users to read crops
-- CREATE POLICY "Allow public read access to crops"
-- ON crops FOR SELECT
-- TO public
-- USING (true);

-- Example policy: Allow authenticated users to insert simulations
-- CREATE POLICY "Allow authenticated insert simulations"
-- ON simulations FOR INSERT
-- TO authenticated
-- WITH CHECK (true);

-- ============================================
-- GRANTS
-- ============================================

-- Grant permissions to authenticated users
GRANT SELECT ON crops TO authenticated;
GRANT SELECT ON terrain_modifiers TO authenticated;
GRANT ALL ON simulations TO authenticated;
GRANT ALL ON user_feedback TO authenticated;