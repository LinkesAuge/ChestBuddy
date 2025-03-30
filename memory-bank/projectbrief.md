# ChestBuddy - Project Brief

## Project Overview

ChestBuddy is a desktop application designed to help players of the "Total Battle" game manage, validate, and analyze chest data. It combines the functionality of previously separate tools (ChestParser and CorrectionTool) into a single, integrated solution with enhanced capabilities for data validation, correction, and visualization.

## Core Requirements

1. **Data Import and Export**
   - Import chest data from CSV files (single or multiple)
   - Support various encodings with special handling for German umlauts
   - Export data in multiple formats for use in other tools
   - Maintain data integrity throughout import/export processes

2. **Data Validation**
   - Validate player names, chest types, and source locations against reference lists
   - Highlight validation issues with clear visual indicators
   - Provide suggestions for corrections based on fuzzy matching
   - Allow manual override of validation rules when needed

3. **Data Correction**
   - Apply batch corrections based on predefined rules
   - Support case-sensitive and case-insensitive corrections
   - Allow creation and modification of correction rules
   - Track correction history for auditing purposes

4. **Data Visualization**
   - Generate informative charts and graphs of chest data
   - Provide multiple visualization types (bar, pie, line)
   - Allow filtering and customization of visualizations
   - Support export of visualizations for sharing

5. **User Experience**
   - Intuitive and modern user interface with Total Battle theming
   - Responsive application even during intensive operations
   - Clear feedback for long-running processes
   - Consistent navigation and interaction patterns

6. **Performance and Reliability**
   - Handle large datasets (10,000+ rows) efficiently
   - Process operations in background threads to maintain UI responsiveness
   - Implement robust error handling and recovery
   - Provide clear progress indication for time-consuming operations

## Target Audience

1. **Individual Players**
   - Track personal chest collection and performance
   - Make optimal gameplay decisions based on data analysis
   - Share data with clan members

2. **Clan Leaders**
   - Track member contributions and activity
   - Analyze clan performance data
   - Make strategic decisions based on data insights

3. **Data Maintainers**
   - Establish consistent naming conventions
   - Maintain correction rules and validation lists
   - Ensure data quality across submissions

## Success Criteria

1. **Functional Success**
   - All core features implemented and working reliably
   - Smooth end-to-end workflows for all user personas
   - Compatibility with existing Total Battle data formats

2. **Technical Success**
   - Clean, maintainable code architecture
   - Comprehensive test coverage
   - Efficient performance with large datasets
   - Reliable operation across supported platforms

3. **User Success**
   - Reduced time spent on data correction and validation
   - Improved insights from data visualization
   - Positive user feedback on workflow and interface
   - Adoption by Total Battle player community

## Constraints and Limitations

1. **Technical Constraints**
   - Windows primary platform (with macOS secondary)
   - Local application with no server-side components
   - Built with Python and PySide6 for UI
   - Pandas for data manipulation

2. **Scope Limitations**
   - No online multiplayer features
   - No direct game integration
   - Manual import of game data (no automatic extraction)
   - Limited to chest data analysis (not general game analytics)

## Project Timeline and Milestones

The project is being developed incrementally with focus on stable, tested features at each phase:

1. **Phase 1-10**: Core functionality implementation (completed)
2. **Phase 11**: Validation service improvements (completed)
3. **Phase 12**: Chart integration (completed)
4. **Phase 13+**: CSV loading improvements and UI enhancements (completed)
5. **Future Phases**: Report generation, performance optimizations, additional analysis features

This project brief serves as the foundation document for the ChestBuddy application and should guide all development decisions and feature implementations. 