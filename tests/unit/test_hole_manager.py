"""
Tests for HoleManager functionality.
"""
import pytest
from src.ui.hole_manager import HoleManager, HolePosition


class TestHoleManager:
    """Test cases for HoleManager class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.hole_manager = HoleManager()
    
    def test_hole_manager_initialization(self):
        """Test HoleManager initialization."""
        assert self.hole_manager.rows == 10
        assert self.hole_manager.cols == 12
        assert self.hole_manager.total_holes == 120
        assert self.hole_manager.hole_width == 90
        assert self.hole_manager.hole_height == 90
        assert self.hole_manager.start_hole_number == 25
    
    def test_number_to_position(self):
        """Test converting hole number to position."""
        # Test first hole (1)
        row, col = self.hole_manager.number_to_position(1)
        assert row == 0
        assert col == 0
        
        # Test last hole (120)
        row, col = self.hole_manager.number_to_position(120)
        assert row == 9
        assert col == 11
        
        # Test middle hole (60)
        row, col = self.hole_manager.number_to_position(60)
        assert row == 4  # (60-1)//12 = 4
        assert col == 11  # (60-1)%12 = 11
        
        # Test invalid hole numbers
        with pytest.raises(ValueError):
            self.hole_manager.number_to_position(0)
        
        with pytest.raises(ValueError):
            self.hole_manager.number_to_position(121)
    
    def test_position_to_number(self):
        """Test converting position to hole number."""
        # Test first position (0, 0)
        hole_number = self.hole_manager.position_to_number(0, 0)
        assert hole_number == 1
        
        # Test last position (9, 11)
        hole_number = self.hole_manager.position_to_number(9, 11)
        assert hole_number == 120
        
        # Test middle position (4, 11)
        hole_number = self.hole_manager.position_to_number(4, 11)
        assert hole_number == 60
        
        # Test invalid positions
        with pytest.raises(ValueError):
            self.hole_manager.position_to_number(-1, 0)
        
        with pytest.raises(ValueError):
            self.hole_manager.position_to_number(10, 0)
        
        with pytest.raises(ValueError):
            self.hole_manager.position_to_number(0, -1)
        
        with pytest.raises(ValueError):
            self.hole_manager.position_to_number(0, 12)
    
    def test_get_row_from_hole_number(self):
        """Test getting row from hole number."""
        assert self.hole_manager.get_row_from_hole_number(1) == 0
        assert self.hole_manager.get_row_from_hole_number(12) == 0
        assert self.hole_manager.get_row_from_hole_number(13) == 1
        assert self.hole_manager.get_row_from_hole_number(60) == 4
        assert self.hole_manager.get_row_from_hole_number(120) == 9
    
    def test_get_col_from_hole_number(self):
        """Test getting column from hole number."""
        assert self.hole_manager.get_col_from_hole_number(1) == 0
        assert self.hole_manager.get_col_from_hole_number(12) == 11
        assert self.hole_manager.get_col_from_hole_number(13) == 0
        assert self.hole_manager.get_col_from_hole_number(60) == 11
        assert self.hole_manager.get_col_from_hole_number(120) == 11
    
    def test_get_hole_coordinates(self):
        """Test getting hole coordinates."""
        # Test first hole (1)
        x, y, width, height = self.hole_manager.get_hole_coordinates(1)
        expected_x = (750 - 90 // 2) + 0 * 145  # 705
        expected_y = (392 - 90 // 2) + 0 * 145  # 347
        assert x == expected_x
        assert y == expected_y
        assert width == 90
        assert height == 90
        
        # Test second hole (2)
        x, y, width, height = self.hole_manager.get_hole_coordinates(2)
        expected_x = (750 - 90 // 2) + 1 * 145  # 850
        expected_y = (392 - 90 // 2) + 0 * 145  # 347
        assert x == expected_x
        assert y == expected_y
        assert width == 90
        assert height == 90
    
    def test_get_hole_center_coordinates(self):
        """Test getting hole center coordinates."""
        # Test first hole (1)
        center_x, center_y = self.hole_manager.get_hole_center_coordinates(1)
        x, y, width, height = self.hole_manager.get_hole_coordinates(1)
        expected_center_x = x + width // 2
        expected_center_y = y + height // 2
        assert center_x == expected_center_x
        assert center_y == expected_center_y
    
    def test_get_hole_info(self):
        """Test getting complete hole information."""
        hole_info = self.hole_manager.get_hole_info(1)
        
        assert isinstance(hole_info, HolePosition)
        assert hole_info.number == 1
        assert hole_info.row == 0
        assert hole_info.col == 0
        assert hole_info.x == 705
        assert hole_info.y == 347
        assert hole_info.width == 90
        assert hole_info.height == 90
    
    def test_get_adjacent_holes(self):
        """Test getting adjacent hole numbers."""
        # Test middle hole (60)
        adjacent = self.hole_manager.get_adjacent_holes(60)
        # Should have left (59), right (61), top (48), bottom (72) neighbors
        assert set(adjacent) == {48, 59, 61, 72}
        
        # Test corner hole (1)
        adjacent = self.hole_manager.get_adjacent_holes(1)
        # Should have right (2) and bottom (13) neighbors
        assert set(adjacent) == {2, 13}
        
        # Test edge hole (12)
        adjacent = self.hole_manager.get_adjacent_holes(12)
        # Should have left (11) and bottom (24) neighbors
        assert set(adjacent) == {11, 24}
    
    def test_update_positioning_params(self):
        """Test updating positioning parameters."""
        # Update some parameters
        self.hole_manager.update_positioning_params(
            first_hole_x=800,
            first_hole_y=400,
            horizontal_spacing=150,
            vertical_spacing=150
        )
        
        # Check that parameters were updated
        assert self.hole_manager.first_hole_x == 800
        assert self.hole_manager.first_hole_y == 400
        assert self.hole_manager.horizontal_spacing == 150
        assert self.hole_manager.vertical_spacing == 150
        
        # Check that dependent parameters were updated
        assert self.hole_manager.hole_spacing_x == 150
        assert self.hole_manager.hole_spacing_y == 150
        
        # Test coordinates with new parameters
        x, y, width, height = self.hole_manager.get_hole_coordinates(1)
        expected_x = (800 - 90 // 2) + 0 * 150  # 755
        expected_y = (400 - 90 // 2) + 0 * 150  # 355
        assert x == expected_x
        assert y == expected_y
    
    def test_set_layout_params_standard(self):
        """Test setting layout parameters for standard panoramic image."""
        # Test with standard 3088x2064 dimensions
        self.hole_manager.set_layout_params(3088, 2064)
        
        # Parameters should remain unchanged since they're already optimized
        assert self.hole_manager.first_hole_x == 750
        assert self.hole_manager.first_hole_y == 392
        assert self.hole_manager.horizontal_spacing == 145
        assert self.hole_manager.vertical_spacing == 145
        assert self.hole_manager.hole_diameter == 90
    
    def test_set_layout_params_custom(self):
        """Test setting layout parameters for custom dimensions."""
        # Test with custom dimensions
        self.hole_manager.set_layout_params(2000, 1500, margin_x=30, margin_y=30)
        
        # Check that parameters were calculated
        assert self.hole_manager.hole_spacing_x > 0
        assert self.hole_manager.hole_spacing_y > 0
        assert self.hole_manager.hole_width > 0
        assert self.hole_manager.hole_height > 0
        assert self.hole_manager.start_x >= 30
        assert self.hole_manager.start_y >= 30