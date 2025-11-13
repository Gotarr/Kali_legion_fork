"""
Tests for Hydra output parser.

Author: Gotham Security
Date: 2025-11-13
"""

import pytest
from pathlib import Path
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from legion.tools.hydra.parser import (
    HydraOutputParser,
    HydraResult,
    HydraCredential,
    HydraStatistics,
)


class TestHydraOutputParser:
    """Test suite for HydraOutputParser."""
    
    @pytest.fixture
    def parser(self):
        """Create a parser instance."""
        return HydraOutputParser()
    
    @pytest.fixture
    def sample_success_output(self):
        """Sample Hydra output with successful credentials."""
        return """
Hydra v9.6 (c) 2023 by van Hauser/THC & David Maciejak - Please do not use in military or secret service organizations, or for illegal purposes (this is non-binding, these *** ignore laws and ethics anyway).

Hydra (https://github.com/vanhauser-thc/thc-hydra) starting at 2025-11-13 10:30:00
[DATA] max 16 tasks per 1 server, overall 16 tasks, 100 login tries (l:10/p:10), ~7 tries per task
[DATA] attacking ssh://192.168.1.1:22/
[22][ssh] host: 192.168.1.1   login: admin   password: admin123
[22][ssh] host: 192.168.1.1   login: root   password: toor
1 of 1 target successfully completed, 2 valid passwords found
Hydra (https://github.com/vanhauser-thc/thc-hydra) finished at 2025-11-13 10:30:15
"""
    
    @pytest.fixture
    def sample_failure_output(self):
        """Sample Hydra output with no credentials found."""
        return """
Hydra v9.6 (c) 2023 by van Hauser/THC & David Maciejak
Hydra (https://github.com/vanhauser-thc/thc-hydra) starting at 2025-11-13 11:00:00
[DATA] max 8 tasks per 1 server, overall 8 tasks, 50 login tries (l:5/p:10), ~7 tries per task
[DATA] attacking ftp://192.168.1.100:21/
0 of 1 target successfully completed, 0 valid passwords found
Hydra (https://github.com/vanhauser-thc/thc-hydra) finished at 2025-11-13 11:00:30
"""
    
    @pytest.fixture
    def sample_error_output(self):
        """Sample Hydra output with errors."""
        return """
Hydra v9.6 (c) 2023 by van Hauser/THC & David Maciejak
[ERROR] target ssh://invalid.host:22/ does not resolve
[ERROR] could not connect to target
[WARNING] Using default password list, this might not be what you want
0 of 1 target completed, 0 valid passwords found
"""
    
    def test_parse_successful_credentials(self, parser, sample_success_output):
        """Test parsing of successful credential discovery."""
        result = parser.parse(sample_success_output)
        
        assert isinstance(result, HydraResult)
        assert result.success is True
        assert result.credential_count == 2
        
        # Check first credential
        cred1 = result.credentials[0]
        assert cred1.host == "192.168.1.1"
        assert cred1.port == 22
        assert cred1.service == "ssh"
        assert cred1.login == "admin"
        assert cred1.password == "admin123"
        
        # Check second credential
        cred2 = result.credentials[1]
        assert cred2.login == "root"
        assert cred2.password == "toor"
    
    def test_parse_statistics(self, parser, sample_success_output):
        """Test parsing of attack statistics."""
        result = parser.parse(sample_success_output)
        
        stats = result.statistics
        assert isinstance(stats, HydraStatistics)
        assert stats.total_attempts == 100  # 10 logins * 10 passwords
        assert stats.successful_attempts == 2
        assert stats.tasks == 16
        assert stats.duration_seconds == 15.0  # 10:30:00 to 10:30:15
        assert stats.attempts_per_second > 0
    
    def test_parse_no_credentials(self, parser, sample_failure_output):
        """Test parsing when no credentials found."""
        result = parser.parse(sample_failure_output)
        
        assert result.success is False
        assert result.credential_count == 0
        assert len(result.credentials) == 0
        assert result.statistics.total_attempts == 50  # 5 * 10
    
    def test_parse_errors_and_warnings(self, parser, sample_error_output):
        """Test parsing of error and warning messages."""
        result = parser.parse(sample_error_output)
        
        assert len(result.errors) == 2
        assert "does not resolve" in result.errors[0]
        assert "could not connect" in result.errors[1]
        
        assert len(result.warnings) == 1
        assert "default password list" in result.warnings[0]
    
    def test_parse_target_service_extraction(self, parser, sample_success_output):
        """Test extraction of target and service from credentials."""
        result = parser.parse(sample_success_output)
        
        assert result.target == "192.168.1.1"
        assert result.service == "ssh"
    
    def test_parse_empty_output(self, parser):
        """Test parsing of empty output."""
        result = parser.parse("")
        
        assert result.credential_count == 0
        assert result.statistics.total_attempts == 0
        assert len(result.errors) == 0
    
    def test_credential_string_representation(self):
        """Test HydraCredential string representation."""
        cred = HydraCredential(
            host="192.168.1.1",
            port=22,
            service="ssh",
            login="admin",
            password="password123"
        )
        
        cred_str = str(cred)
        assert "admin:password123" in cred_str
        assert "ssh://192.168.1.1:22" in cred_str
    
    def test_result_to_dict(self, parser, sample_success_output):
        """Test conversion of HydraResult to dictionary."""
        result = parser.parse(sample_success_output)
        
        result_dict = result.to_dict()
        
        assert isinstance(result_dict, dict)
        assert "credentials" in result_dict
        assert "statistics" in result_dict
        assert len(result_dict["credentials"]) == 2
        assert result_dict["statistics"]["successful_attempts"] == 2
    
    def test_parse_ftp_credentials(self, parser):
        """Test parsing FTP credentials."""
        output = """
[21][ftp] host: ftp.example.com   login: ftpuser   password: ftppass123
"""
        result = parser.parse(output)
        
        assert result.credential_count == 1
        cred = result.credentials[0]
        assert cred.port == 21
        assert cred.service == "ftp"
        assert cred.login == "ftpuser"
        assert cred.password == "ftppass123"
    
    def test_parse_http_post_form(self, parser):
        """Test parsing HTTP POST form credentials."""
        output = """
[80][http-post-form] host: 192.168.1.50   login: webadmin   password: web123
"""
        result = parser.parse(output)
        
        assert result.credential_count == 1
        cred = result.credentials[0]
        assert cred.service == "http-post-form"
        assert cred.login == "webadmin"
    
    def test_parse_password_with_spaces(self, parser):
        """Test parsing passwords containing spaces."""
        output = """
[22][ssh] host: 192.168.1.1   login: user   password: pass with spaces
"""
        result = parser.parse(output)
        
        assert result.credential_count == 1
        assert result.credentials[0].password == "pass with spaces"
    
    def test_statistics_string_representation(self):
        """Test HydraStatistics string representation."""
        stats = HydraStatistics(
            total_attempts=100,
            successful_attempts=2,
            duration_seconds=15.5,
            attempts_per_second=6.45,
            tasks=16
        )
        
        stats_str = str(stats)
        assert "2/100" in stats_str
        assert "6.5/s" in stats_str or "6.4/s" in stats_str
        assert "15.5s" in stats_str
    
    def test_result_string_representation(self, parser, sample_success_output):
        """Test HydraResult string representation."""
        result = parser.parse(sample_success_output)
        
        result_str = str(result)
        assert "✓" in result_str or "Found" in result_str
        assert "2 credential" in result_str
    
    def test_parse_multiple_services(self, parser):
        """Test parsing multiple different services in one output."""
        output = """
[22][ssh] host: 192.168.1.1   login: admin   password: ssh123
[21][ftp] host: 192.168.1.1   login: admin   password: ftp123
[3306][mysql] host: 192.168.1.1   login: root   password: mysql123
"""
        result = parser.parse(output)
        
        assert result.credential_count == 3
        services = [cred.service for cred in result.credentials]
        assert "ssh" in services
        assert "ftp" in services
        assert "mysql" in services


class TestHydraCredential:
    """Test HydraCredential dataclass."""
    
    def test_credential_creation(self):
        """Test creating a credential."""
        cred = HydraCredential(
            host="test.host",
            port=22,
            service="ssh",
            login="user",
            password="pass"
        )
        
        assert cred.host == "test.host"
        assert cred.port == 22
        assert cred.service == "ssh"
        assert cred.login == "user"
        assert cred.password == "pass"


class TestHydraStatistics:
    """Test HydraStatistics dataclass."""
    
    def test_statistics_defaults(self):
        """Test default values for statistics."""
        stats = HydraStatistics()
        
        assert stats.total_attempts == 0
        assert stats.successful_attempts == 0
        assert stats.duration_seconds == 0.0
        assert stats.attempts_per_second == 0.0
        assert stats.tasks == 0


class TestHydraResult:
    """Test HydraResult dataclass."""
    
    def test_result_empty(self):
        """Test empty result."""
        result = HydraResult()
        
        assert result.success is False
        assert result.credential_count == 0
        assert len(result.credentials) == 0
    
    def test_result_with_credentials(self):
        """Test result with credentials."""
        cred = HydraCredential(
            host="test.host",
            port=22,
            service="ssh",
            login="user",
            password="pass"
        )
        
        result = HydraResult(credentials=[cred])
        
        assert result.success is True
        assert result.credential_count == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
