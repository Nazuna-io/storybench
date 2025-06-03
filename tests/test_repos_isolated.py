"""Test database repository functionality in isolation."""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@pytest.fixture
def mock_db_session():
    """Create a mock database session."""
    session = MagicMock()
    session.query.return_value = session
    session.filter.return_value = session
    session.first.return_value = None
    session.all.return_value = []
    session.add.return_value = None
    session.commit.return_value = None
    session.rollback.return_value = None
    return session


def test_criteria_repo_basic_operations(mock_db_session):
    """Test criteria repository basic operations."""
    try:
        from storybench.database.repositories.criteria_repo import CriteriaRepository
        
        repo = CriteriaRepository()
        
        # Mock the session
        with patch.object(repo, '_get_session', return_value=mock_db_session):
            # Test get_all
            result = repo.get_all()
            assert result == []
            mock_db_session.query.assert_called()
            
            # Test get_by_id
            result = repo.get_by_id(1)
            assert result is None
            
    except ImportError as e:
        pytest.skip(f"Skipping due to missing dependencies: {e}")


def test_model_repo_basic_operations(mock_db_session):
    """Test model repository basic operations."""
    try:
        from storybench.database.repositories.model_repo import ModelRepository
        
        repo = ModelRepository()
        
        # Mock the session
        with patch.object(repo, '_get_session', return_value=mock_db_session):
            result = repo.get_all()
            assert result == []
            
    except ImportError as e:
        pytest.skip(f"Skipping due to missing dependencies: {e}")
