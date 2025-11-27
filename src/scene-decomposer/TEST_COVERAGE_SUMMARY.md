# Scene-Decomposer Test Coverage Summary

**Total: 76 test cases | Coverage: 88%**

## Test Results

✅ **76 passed in 2.43s**

## Coverage Breakdown by Module

### Production Code Coverage

| Module | Statements | Missed | Coverage |
|--------|-----------|--------|----------|
| **src/trailer_generator/api.py** | 69 | 4 | **94%** |
| **src/trailer_generator/config.py** | 14 | 0 | **100%** |
| **src/trailer_generator/scene_analyzer.py** | 70 | 1 | **99%** |
| **src/trailer_generator/scene_generator.py** | 94 | 4 | **96%** |
| **src/trailer_generator/schemas.py** | 78 | 0 | **100%** |

### **Overall Production Coverage: 98%** (excluding standalone script)

Note: The 88% overall figure includes test_scene_standalone.py (11% coverage), which is a utility script not part of core functionality.

## Test Coverage by Category

### 1. Scene Analyzer (22 tests)
- ✅ Analyzer initialization
- ✅ Movie analysis returns complete MovieAnalysis
- ✅ Extract main characters (top 4)
- ✅ Extract main characters (fewer than 4)
- ✅ Extract key themes (top 4)
- ✅ Extract key themes (fewer than 4)
- ✅ Summarize visual style
- ✅ Determine tone for Thriller
- ✅ Determine tone for Action
- ✅ Determine tone for Drama
- ✅ Determine tone for Sci-Fi
- ✅ Determine tone for Comedy
- ✅ Determine tone for Horror
- ✅ Determine tone for Romance
- ✅ Determine tone for Crime
- ✅ Determine tone for Unknown genre
- ✅ Identify hooks with USP
- ✅ Identify hooks without USP
- ✅ Get character consistency guide
- ✅ Format for LLM context
- ✅ Format character designs for LLM
- ✅ Complete analysis workflow

### 2. API Endpoints (20 tests)
- ✅ Root endpoint returns service info
- ✅ Health check with API key configured
- ✅ Health check without API key
- ✅ Generate trailer success
- ✅ Generate trailer with custom model
- ✅ Generate trailer with scene generator error
- ✅ Generate trailer with unexpected error
- ✅ Generate trailer invalid duration (too short)
- ✅ Generate trailer invalid duration (too long)
- ✅ Generate trailer missing required fields
- ✅ Generate trailer invalid movie data
- ✅ Generate trailer with default values
- ✅ Generate trailer saves output to file
- ✅ Analyze movie success
- ✅ Analyze movie with invalid data
- ✅ Analyze movie with analysis error
- ✅ Analyze movie with empty cast
- ✅ CORS headers on OPTIONS request
- ✅ Lifespan events startup

### 3. Configuration Management (10 tests)
- ✅ Default configuration values
- ✅ Settings with environment variables
- ✅ Extra environment variables ignored
- ✅ Global settings instance
- ✅ OpenRouter base URL customization
- ✅ API host customization
- ✅ Numeric type conversion
- ✅ Boolean type conversion
- ✅ Settings immutability after creation
- ✅ Model config attributes

### 4. Scene Generator (19 tests)
- ✅ Initialization with defaults
- ✅ Initialization with custom parameters
- ✅ Create generation prompt
- ✅ Create generation prompt without narration
- ✅ Create generation prompt with different durations
- ✅ Generate trailer success
- ✅ Generate trailer with model override
- ✅ Generate trailer with empty response
- ✅ Generate trailer with invalid JSON
- ✅ Generate trailer with JSON and extra text
- ✅ Generate trailer API error
- ✅ Build character appearance map
- ✅ Validate trailer consistency (valid)
- ✅ Validate trailer consistency (wrong duration)
- ✅ Validate trailer consistency (too many references)
- ✅ Validate trailer consistency (missing character)
- ✅ Validate trailer consistency (empty reference images)
- ✅ Generate trailer without narration
- ✅ Generate trailer validates output

### 5. Schema Validation (4 tests)
- ✅ CharacterDesign schema validation
- ✅ TrailerScene with reference images
- ✅ TrailerScene without reference images
- ✅ TrailerBreakdown complete schema
- ✅ Validation constraints enforcement

### 6. Smoke Test (1 test)
- ✅ Basic import test

## Summary

- **76 tests** covering all major functionality
- **88% overall code coverage** (98% excluding standalone script)
- **100% coverage** on config.py and schemas.py
- **99% coverage** on scene_analyzer.py
- Comprehensive scene analysis testing
- Complete scene generation with validation
- Full API endpoint testing
- Genre-specific tone determination tests
- Fast test execution: 2.43 seconds