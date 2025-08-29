# Panoramic Annotation Tool - Comprehensive Test Plan

This document outlines a comprehensive testing strategy for the Panoramic Annotation Tool, covering all aspects of the application from data models to user interface interactions.

## 1. Test Scope

The test plan covers the following components of the Panoramic Annotation Tool:

1. **Data Models**
   - PanoramicAnnotation
   - EnhancedPanoramicAnnotation
   - FeatureCombination
   - HolePosition
   - Related enums (GrowthLevel, GrowthPattern, InterferenceType)

2. **Core Services**
   - HoleManager
   - PanoramicImageService
   - ConfigFileService

3. **UI Components**
   - PanoramicAnnotationGUI (main application)
   - EnhancedAnnotationPanel
   - HoleConfigPanel
   - BatchImportDialog

4. **Workflow Integration**
   - Data loading and initialization
   - Hole navigation
   - Annotation creation and modification
   - Data persistence
   - Export functionality

## 2. Test Categories

### 2.1 Unit Tests

#### 2.1.1 Data Model Tests

**PanoramicAnnotation Tests**
- Creation with valid and invalid parameters
- Validation of hole number (1-120)
- Validation of microbe type (bacteria/fungi)
- Validation of growth level (negative/weak_growth/positive)
- Filename parsing (independent and subdirectory modes)
- Adjacent hole calculation
- Serialization/deserialization

**EnhancedPanoramicAnnotation Tests**
- Feature combination creation and manipulation
- Interference factor addition/removal
- Growth pattern setting
- Label generation
- Serialization/deserialization

**HoleManager Tests**
- Hole number to position conversion
- Position to hole number conversion
- Coordinate calculation
- Adjacent hole detection
- Layout parameter configuration

#### 2.1.2 Service Tests

**PanoramicImageService Tests**
- Image loading from various formats
- Panoramic image processing
- Slice image extraction
- Image information retrieval

**ConfigFileService Tests**
- Configuration file loading
- Default configuration generation
- Configuration validation

### 2.2 Integration Tests

#### 2.2.1 Data Flow Tests
- Loading panoramic images from directory
- Parsing hole information from filenames
- Creating annotation objects from image data
- Saving annotations to JSON files
- Loading annotations from JSON files

#### 2.2.2 Navigation Tests
- Navigating between holes using arrow keys
- Direct hole number input
- Panoramic image navigation
- Slice image display updates

#### 2.2.3 Annotation Tests
- Setting growth levels
- Selecting microbe types
- Adding interference factors
- Creating enhanced annotations
- Annotation persistence

### 2.3 UI Tests

#### 2.3.1 Component Tests
- Panoramic image display
- Slice image display
- Annotation panel controls
- Navigation controls
- Import/export dialogs

#### 2.3.2 Interaction Tests
- Mouse click navigation
- Keyboard shortcut handling
- Form input validation
- Button click responses

### 2.4 Workflow Tests

#### 2.4.1 End-to-End Tests
- Complete annotation workflow from start to finish
- Batch import functionality
- Export to various formats
- Configuration management

#### 2.4.2 Error Handling Tests
- Invalid directory selection
- Corrupted image files
- Missing configuration files
- Insufficient permissions

## 3. Test Scenarios

### 3.1 Data Model Scenarios

#### 3.1.1 PanoramicAnnotation Creation
```
GIVEN a valid panoramic image filename
WHEN creating a PanoramicAnnotation object
THEN all properties should be correctly initialized
AND validation should pass for valid inputs
AND validation should fail for invalid inputs
```

#### 3.1.2 Filename Parsing
```
GIVEN a filename in independent mode (EB10000026_hole_108.png)
WHEN parsing the filename
THEN panoramic_id should be "EB10000026"
AND hole_number should be 108
AND row/col should be calculated correctly

GIVEN a filename in subdirectory mode (hole_108.png) with panoramic_id
WHEN parsing the filename
THEN panoramic_id should be provided value
AND hole_number should be 108
AND row/col should be calculated correctly
```

#### 3.1.3 Adjacent Hole Calculation
```
GIVEN a hole in the middle of the grid (hole 60)
WHEN calculating adjacent holes
THEN left (59), right (61), top (48), and bottom (72) should be returned

GIVEN a corner hole (hole 1)
WHEN calculating adjacent holes
THEN only right (2) and bottom (13) should be returned
```

### 3.2 UI Scenarios

#### 3.2.1 Hole Navigation
```
GIVEN the application is loaded with panoramic images
WHEN the user presses the right arrow key
THEN the next hole should be selected
AND the slice image should update
AND the annotation panel should update

GIVEN the user enters a hole number in the input field
WHEN they press Enter
THEN the specified hole should be selected
AND all UI components should update accordingly
```

#### 3.2.2 Annotation Creation
```
GIVEN a hole is selected
WHEN the user selects "positive" growth level
AND selects "bacteria" microbe type
AND clicks "Save Annotation"
THEN the annotation should be saved
AND the UI should reflect the saved state
```

### 3.3 Workflow Scenarios

#### 3.3.1 Complete Annotation Session
```
GIVEN a fresh application start
WHEN the user loads a panoramic directory
AND annotates several holes
AND saves the annotations
THEN the annotations should be persisted to disk
AND can be loaded in a subsequent session
```

#### 3.3.2 Batch Import
```
GIVEN existing annotation configuration files
WHEN the user selects batch import
AND selects a configuration file
THEN annotations should be imported
AND applied to the corresponding holes
```

## 4. Test Data Requirements

### 4.1 Test Images
- Sample panoramic images (3088×2064 pixels)
- Various hole patterns (negative, weak growth, positive)
- Images with interference factors (pores, artifacts, edge blur)
- Different microbe types (bacteria, fungi)

### 4.2 Test Configurations
- Valid configuration files
- Invalid configuration files
- Configuration files with missing fields
- Configuration files with incorrect data types

### 4.3 Test Directories
- Empty directories
- Directories with mixed file types
- Directories with subdirectories
- Directories with permission restrictions

## 5. Test Execution Plan

### 5.1 Automated Tests
- Unit tests for all data models and services
- Integration tests for data flow
- UI component tests
- Workflow tests

### 5.2 Manual Tests
- Visual verification of image display
- User experience evaluation
- Keyboard shortcut testing
- Edge case scenarios

### 5.3 Performance Tests
- Image loading times
- Annotation saving times
- Memory usage during operation
- Response times for navigation

## 6. Test Environment

### 6.1 Hardware Requirements
- Minimum: 4GB RAM, 2GHz processor
- Recommended: 8GB RAM, 3GHz processor
- Storage: 100MB free space minimum

### 6.2 Software Requirements
- Python 3.8+
- Required Python packages (Pillow, tkinter, pathlib, etc.)
- Windows 10/11, macOS, or Linux

### 6.3 Test Data Setup
- Automated generation of test images
- Sample configuration files
- Predefined annotation datasets

## 7. Test Metrics

### 7.1 Quality Metrics
- Code coverage: >90%
- Test pass rate: >95%
- Defect detection rate: >80%

### 7.2 Performance Metrics
- Image loading time: <2 seconds
- Annotation save time: <1 second
- Memory usage: <500MB during normal operation

### 7.3 User Experience Metrics
- Navigation response time: <0.5 seconds
- UI update time: <0.3 seconds
- Error message clarity rating: >4/5

## 8. Test Tools and Frameworks

### 8.1 Unit Testing
- pytest for Python unit tests
- Mock objects for dependency isolation

### 8.2 UI Testing
- tkinter for UI component testing
- Custom test harness for integration testing

### 8.3 Automation
- Custom test runners
- Automated test data generation
- Continuous integration scripts

## 9. Test Schedule

### 9.1 Phase 1: Unit Tests (Week 1)
- Data model tests
- Service tests
- Basic validation

### 9.2 Phase 2: Integration Tests (Week 2)
- Data flow tests
- Component integration
- Basic workflow tests

### 9.3 Phase 3: UI Tests (Week 3)
- Component tests
- Interaction tests
- Visual verification

### 9.4 Phase 4: End-to-End Tests (Week 4)
- Complete workflow tests
- Performance tests
- User acceptance tests

## 10. Risk Mitigation

### 10.1 Technical Risks
- Image processing failures
- Memory leaks
- Performance degradation

### 10.2 Test Risks
- Incomplete test coverage
- Flaky tests
- Environment dependencies

### 10.3 Mitigation Strategies
- Regular code reviews
- Continuous integration
- Performance monitoring
- Test environment standardization

## 11. Test Deliverables

### 11.1 Test Documentation
- This test plan
- Test case specifications
- Test execution reports
- Defect reports

### 11.2 Test Automation
- Automated test suites
- Test data generators
- Reporting tools

### 11.3 Test Environment
- Standardized test environments
- Test data repositories
- Performance baselines

## 12. Approval

This test plan requires approval from the development team and project stakeholders before implementation.

**Prepared by:** [Test Lead]
**Date:** [Current Date]
**Approved by:** [Project Manager]
**Approval Date:** [TBD]