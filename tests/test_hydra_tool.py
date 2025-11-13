"""
Integration tests for Hydra tool wrapper.

Note: These tests require Hydra to be installed and available in the system.
Tests will be skipped if Hydra is not found.

Author: Gotham Security
Date: 2025-11-13
"""

import pytest
import asyncio
from pathlib import Path
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from legion.tools.hydra import HydraTool, HydraResult
from legion.tools.registry import ToolRegistry


class TestHydraTool:
    """Test suite for HydraTool wrapper."""
    
    @pytest.fixture
    async def hydra(self):
        """Create a Hydra tool instance."""
        tool = HydraTool()
        return tool
    
    @pytest.fixture
    def registry(self):
        """Create a tool registry instance."""
        return ToolRegistry()
    
    @pytest.mark.asyncio
    async def test_tool_initialization(self):
        """Test Hydra tool initialization."""
        hydra = HydraTool()
        
        assert hydra.tool_name == "hydra"
        # Tool path may be None if not installed
    
    @pytest.mark.asyncio
    async def test_tool_discovery(self, registry):
        """Test Hydra discovery via registry."""
        hydra_path = registry.get_tool("hydra")
        
        # Note: Test might fail if Hydra not installed
        if hydra_path:
            assert hydra_path.exists()
            assert "hydra" in str(hydra_path).lower()
    
    @pytest.mark.asyncio
    async def test_tool_validation(self, hydra):
        """Test Hydra validation."""
        if hydra.tool_path:
            is_valid = await hydra.validate()
            # Should be valid if path exists
            assert isinstance(is_valid, bool)
    
    @pytest.mark.asyncio
    async def test_version_extraction(self, hydra):
        """Test version extraction from Hydra."""
        if hydra.tool_path:
            version = await hydra.get_version()
            
            assert version != "unknown"
            # Hydra version format: "9.6"
            assert len(version) > 0
    
    @pytest.mark.asyncio
    async def test_get_info(self, hydra):
        """Test getting tool info."""
        if hydra.tool_path:
            info = await hydra.get_info()
            
            assert info.name == "hydra"
            assert info.path == hydra.tool_path
            assert info.available is True
    
    @pytest.mark.asyncio
    async def test_attack_parameter_validation(self, hydra):
        """Test attack parameter validation."""
        if not hydra.tool_path:
            pytest.skip("Hydra not installed")
        
        # Should raise ValueError without login source
        with pytest.raises(ValueError):
            await hydra.attack(
                target="127.0.0.1",
                service="ssh",
                password_list=["test"]
                # Missing login_list or login_file
            )
        
        # Should raise ValueError without password source
        with pytest.raises(ValueError):
            await hydra.attack(
                target="127.0.0.1",
                service="ssh",
                login_list=["test"]
                # Missing password_list or password_file
            )
    
    @pytest.mark.asyncio
    async def test_attack_command_building(self, hydra):
        """Test command building for attack."""
        if not hydra.tool_path:
            pytest.skip("Hydra not installed")
        
        # Mock attack (will fail but tests command building)
        # Use a non-routable IP to avoid actual network traffic
        try:
            result = await hydra.attack(
                target="192.0.2.1",  # TEST-NET-1 (RFC 5737)
                service="ssh",
                login_list=["admin"],
                password_list=["test"],
                tasks=1,
                timeout=1.0  # Short timeout
            )
            
            # Check command was built correctly
            assert "192.0.2.1" in " ".join(result.command)
            assert "ssh" in " ".join(result.command)
            assert "-l" in result.command or "admin" in " ".join(result.command)
            assert "-p" in result.command or "test" in " ".join(result.command)
            assert "-t" in result.command
            
        except asyncio.TimeoutError:
            # Timeout is expected
            pass
    
    @pytest.mark.asyncio
    async def test_parse_output(self, hydra):
        """Test output parsing."""
        # Create mock ToolResult with sample output
        from legion.tools.base import ToolResult
        
        sample_output = """
[22][ssh] host: 192.168.1.1   login: admin   password: admin123
1 of 1 target successfully completed, 1 valid password found
"""
        
        mock_result = ToolResult(
            success=True,
            exit_code=0,
            stdout=sample_output,
            stderr="",
            command=["hydra"],
            duration=1.0
        )
        
        parsed = await hydra.parse_output(mock_result)
        
        assert isinstance(parsed, HydraResult)
        assert parsed.credential_count == 1
        assert parsed.credentials[0].login == "admin"
        assert parsed.credentials[0].password == "admin123"
    
    def test_version_extraction_format(self, hydra):
        """Test version string extraction."""
        sample_version = "Hydra v9.6 (c) 2023 by van Hauser/THC"
        
        version = hydra._extract_version(sample_version)
        
        assert "9.6" in version
    
    @pytest.mark.asyncio
    async def test_attack_with_port(self, hydra):
        """Test attack with custom port."""
        if not hydra.tool_path:
            pytest.skip("Hydra not installed")
        
        try:
            result = await hydra.attack(
                target="192.0.2.1",
                service="ssh",
                login_list=["admin"],
                password_list=["test"],
                port=2222,  # Custom port
                tasks=1,
                timeout=1.0
            )
            
            # Check port was added to command
            assert "-s" in result.command
            assert "2222" in result.command
            
        except asyncio.TimeoutError:
            pass
    
    @pytest.mark.asyncio
    async def test_attack_with_combo_file(self, hydra, tmp_path):
        """Test attack with combo file (user:pass format)."""
        if not hydra.tool_path:
            pytest.skip("Hydra not installed")
        
        # Create temporary combo file
        combo_file = tmp_path / "combo.txt"
        combo_file.write_text("admin:admin123\nroot:toor\n")
        
        try:
            result = await hydra.attack(
                target="192.0.2.1",
                service="ssh",
                combo_file=combo_file,
                tasks=1,
                timeout=1.0
            )
            
            # Check combo file was used
            assert "-C" in result.command
            assert str(combo_file) in " ".join(result.command)
            
        except asyncio.TimeoutError:
            pass


class TestHydraToolIntegration:
    """Integration tests requiring actual Hydra installation."""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_hydra_help(self):
        """Test running Hydra with help flag."""
        hydra = HydraTool()
        
        if not hydra.tool_path:
            pytest.skip("Hydra not installed")
        
        # Run hydra with -h (help)
        result = await hydra.run(["-h"], timeout=5.0)
        
        # Help should succeed
        # Note: Hydra returns exit code 255 for -h, not 0
        assert "hydra" in result.stdout.lower() or "usage" in result.stdout.lower()
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_hydra_version(self):
        """Test getting Hydra version."""
        hydra = HydraTool()
        
        if not hydra.tool_path:
            pytest.skip("Hydra not installed")
        
        version = await hydra.get_version()
        
        assert version != "unknown"
        # Hydra version should be numeric like "9.6" or "9.5"
        assert any(char.isdigit() for char in version)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "not integration"])
