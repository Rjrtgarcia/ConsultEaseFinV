#!/usr/bin/env python3
"""
Database Startup Check for ConsultEase

This script performs comprehensive database validation and repair before
system startup to prevent database connection failures.
"""

import os
import sys
import logging
import time
from pathlib import Path

# Add the central_system directory to Python path
script_dir = Path(__file__).parent
project_root = script_dir.parent
central_system_path = project_root / "central_system"
sys.path.insert(0, str(central_system_path))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main startup check function."""
    logger.info("🚀 ConsultEase Database Startup Check")
    logger.info("="*50)
    
    try:
        # Import diagnostics tool
        from utils.database_diagnostics import DatabaseDiagnostics
        
        # Initialize diagnostics
        db_path = "consultease.db"
        diagnostics = DatabaseDiagnostics(db_path)
        
        logger.info("🔍 Running comprehensive database diagnostics...")
        
        # Run full diagnostics
        results = diagnostics.run_full_diagnostics()
        
        # Check if any critical issues were found
        critical_issues = []
        
        # Check filesystem issues
        fs_check = results.get('filesystem_check', {})
        if not fs_check.get('permissions_ok', False):
            critical_issues.extend(fs_check.get('issues', []))
        
        # Check file validation issues
        file_check = results.get('file_validation', {})
        if not file_check.get('file_exists', False) or not file_check.get('sqlite_header_valid', False):
            critical_issues.extend(file_check.get('issues', []))
        
        # Check connection issues
        conn_check = results.get('connection_test', {})
        if not conn_check.get('connection_successful', False):
            critical_issues.extend(conn_check.get('issues', []))
        
        # Check schema issues
        schema_check = results.get('schema_validation', {})
        if not schema_check.get('schema_valid', False):
            critical_issues.extend(schema_check.get('issues', []))
        
        # If critical issues found, attempt repair
        if critical_issues:
            logger.warning("⚠️ Critical database issues detected:")
            for issue in critical_issues:
                logger.warning(f"  • {issue}")
            
            logger.info("🔧 Attempting automatic database repair...")
            
            if diagnostics.repair_database():
                logger.info("✅ Database repair completed successfully")
                
                # Run diagnostics again to verify repair
                logger.info("🔍 Verifying database repair...")
                verification_results = diagnostics.run_full_diagnostics()
                
                # Check if repair was successful
                repair_successful = True
                
                fs_check = verification_results.get('filesystem_check', {})
                file_check = verification_results.get('file_validation', {})
                conn_check = verification_results.get('connection_test', {})
                schema_check = verification_results.get('schema_validation', {})
                
                if not (fs_check.get('permissions_ok', False) and 
                        file_check.get('file_exists', False) and
                        file_check.get('sqlite_header_valid', False) and
                        conn_check.get('connection_successful', False) and
                        schema_check.get('schema_valid', False)):
                    repair_successful = False
                
                if repair_successful:
                    logger.info("✅ Database repair verification passed")
                    logger.info("🚀 Database is ready for system startup")
                    return 0
                else:
                    logger.error("❌ Database repair verification failed")
                    logger.error("💥 System startup aborted - manual intervention required")
                    return 1
            else:
                logger.error("❌ Database repair failed")
                logger.error("💥 System startup aborted - manual intervention required")
                return 1
        else:
            logger.info("✅ Database diagnostics passed - no critical issues detected")
            logger.info("🚀 Database is ready for system startup")
            return 0
            
    except ImportError as e:
        logger.error(f"❌ Failed to import diagnostics tool: {e}")
        logger.error("💥 System startup aborted - check Python path and dependencies")
        return 1
    except Exception as e:
        logger.error(f"❌ Unexpected error during database startup check: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        logger.error("💥 System startup aborted - manual intervention required")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
