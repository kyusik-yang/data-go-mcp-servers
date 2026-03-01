"""Integration-style tests for MCP server tools."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock


@pytest.fixture(autouse=True)
def mock_env(monkeypatch):
    monkeypatch.setenv("ASSEMBLY_API_KEY", "test-api-key-1234")


def _make_mock_client(rows: list, method: str):
    """AssemblyAPIClient의 특정 메서드를 mock으로 대체하는 헬퍼."""
    mock_client = AsyncMock()
    getattr(mock_client, method).return_value = rows
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    return mock_client


class TestSearchBillsTool:
    @pytest.mark.asyncio
    async def test_returns_bills_on_success(self):
        from data_go_mcp.open_assembly.server import search_bills

        sample_rows = [{"BILL_NO": "2200001", "BILL_NAME": "테스트법률안", "RST_PROPOSER": "홍길동"}]
        mock_client = _make_mock_client(sample_rows, "search_bills")

        with patch("data_go_mcp.open_assembly.server.AssemblyAPIClient", return_value=mock_client):
            result = await search_bills(age="22", bill_name="테스트")

        assert result["count"] == 1
        assert result["bills"][0]["BILL_NO"] == "2200001"
        assert "error" not in result

    @pytest.mark.asyncio
    async def test_returns_empty_on_no_results(self):
        from data_go_mcp.open_assembly.server import search_bills

        mock_client = _make_mock_client([], "search_bills")

        with patch("data_go_mcp.open_assembly.server.AssemblyAPIClient", return_value=mock_client):
            result = await search_bills(age="22", bill_name="존재하지않음")

        assert result["count"] == 0
        assert result["bills"] == []

    @pytest.mark.asyncio
    async def test_handles_api_error_gracefully(self):
        from data_go_mcp.open_assembly.server import search_bills

        mock_client = AsyncMock()
        mock_client.search_bills.side_effect = ValueError("API error ERROR-290: 인증키 오류")
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("data_go_mcp.open_assembly.server.AssemblyAPIClient", return_value=mock_client):
            result = await search_bills(age="22")

        assert "error" in result
        assert result["bills"] == []


class TestGetBillDetailTool:
    @pytest.mark.asyncio
    async def test_returns_bill_on_found(self):
        from data_go_mcp.open_assembly.server import get_bill_detail

        sample_bill = {"BILL_NO": "2200001", "BILL_NM": "테스트법률안", "PPSR_NM": "홍길동"}
        mock_client = _make_mock_client([sample_bill], "get_bill_detail")

        with patch("data_go_mcp.open_assembly.server.AssemblyAPIClient", return_value=mock_client):
            result = await get_bill_detail(bill_no="2200001")

        assert result["bill"]["BILL_NO"] == "2200001"

    @pytest.mark.asyncio
    async def test_returns_none_on_not_found(self):
        from data_go_mcp.open_assembly.server import get_bill_detail

        mock_client = _make_mock_client([], "get_bill_detail")

        with patch("data_go_mcp.open_assembly.server.AssemblyAPIClient", return_value=mock_client):
            result = await get_bill_detail(bill_no="9999999")

        assert result["bill"] is None


class TestGetMemberInfoTool:
    @pytest.mark.asyncio
    async def test_returns_members(self):
        from data_go_mcp.open_assembly.server import get_member_info

        sample_rows = [{"HG_NM": "홍길동", "POLY_NM": "더불어민주당", "CMIT_NM": "법제사법위원회"}]
        mock_client = _make_mock_client(sample_rows, "get_member_info")

        with patch("data_go_mcp.open_assembly.server.AssemblyAPIClient", return_value=mock_client):
            result = await get_member_info(age="22", name="홍길동")

        assert result["count"] == 1
        assert result["members"][0]["HG_NM"] == "홍길동"

    @pytest.mark.asyncio
    async def test_unit_cd_mapping(self):
        """대수 문자열이 올바른 UNIT_CD로 변환되는지 확인."""
        from data_go_mcp.open_assembly.server import get_member_info

        mock_client = _make_mock_client([], "get_member_info")

        with patch("data_go_mcp.open_assembly.server.AssemblyAPIClient", return_value=mock_client):
            await get_member_info(age="21")

        call_kwargs = mock_client.get_member_info.call_args
        assert call_kwargs.kwargs["unit_cd"] == "100021"


class TestGetBillProposersTool:
    @pytest.mark.asyncio
    async def test_returns_proposers_by_bill_id(self):
        from data_go_mcp.open_assembly.server import get_bill_proposers

        sample_rows = [
            {"PPSR_NM": "홍길동", "PPSR_POLY_NM": "더불어민주당", "REP_DIV": "대표발의", "PPSR_ROLE": "발의자"},
            {"PPSR_NM": "김철수", "PPSR_POLY_NM": "더불어민주당", "REP_DIV": "공동발의", "PPSR_ROLE": "발의자"},
        ]
        mock_client = _make_mock_client(sample_rows, "get_bill_proposers")

        with patch("data_go_mcp.open_assembly.server.AssemblyAPIClient", return_value=mock_client):
            result = await get_bill_proposers(bill_id="PRC_Y2Z6X0Y2W1X9V1W1D4E4D3B7B8Z1A1")

        assert result["count"] == 2
        assert result["proposers"][0]["PPSR_NM"] == "홍길동"
        assert "error" not in result

    @pytest.mark.asyncio
    async def test_uses_bill_id_param(self):
        """BILLINFOPPSR는 BILL_ID 파라미터를 사용해야 함."""
        from data_go_mcp.open_assembly.server import get_bill_proposers

        mock_client = _make_mock_client([], "get_bill_proposers")

        with patch("data_go_mcp.open_assembly.server.AssemblyAPIClient", return_value=mock_client):
            await get_bill_proposers(bill_id="PRC_TEST123")

        call_kwargs = mock_client.get_bill_proposers.call_args
        assert call_kwargs.kwargs["bill_id"] == "PRC_TEST123"


class TestGetCommitteeMembersTool:
    @pytest.mark.asyncio
    async def test_returns_committee_members(self):
        from data_go_mcp.open_assembly.server import get_committee_members

        sample_rows = [
            {"HG_NM": "홍길동", "POLY_NM": "더불어민주당", "CMIT_NM": "법제사법위원회"},
        ]
        mock_client = _make_mock_client(sample_rows, "get_committee_members")

        with patch("data_go_mcp.open_assembly.server.AssemblyAPIClient", return_value=mock_client):
            result = await get_committee_members(age="22", committee="법제사법위원회")

        assert result["count"] == 1
        assert result["members"][0]["CMIT_NM"] == "법제사법위원회"


class TestUnavailableTools:
    @pytest.mark.asyncio
    async def test_search_minutes_returns_not_supported(self):
        from data_go_mcp.open_assembly.server import search_minutes

        result = await search_minutes()
        assert "error" in result
        assert result["count"] == 0
        assert "확인되지 않았습니다" in result["message"]

    @pytest.mark.asyncio
    async def test_get_petitions_returns_not_supported(self):
        from data_go_mcp.open_assembly.server import get_petitions

        result = await get_petitions()
        assert "error" in result
        assert result["count"] == 0
        assert "확인되지 않았습니다" in result["message"]

    @pytest.mark.asyncio
    async def test_get_bill_content_returns_not_supported(self):
        from data_go_mcp.open_assembly.server import get_bill_content

        result = await get_bill_content(bill_id="PRC_TEST")
        assert "error" in result
        assert result["content"] is None
        assert "확인되지 않았습니다" in result["message"]


class TestGetVoteResultsTool:
    @pytest.mark.asyncio
    async def test_returns_vote_results(self):
        from data_go_mcp.open_assembly.server import get_vote_results

        sample_rows = [
            {
                "BILL_NO": "2200001",
                "BILL_NAME": "테스트법안",
                "MEMBER_TCNT": "300",
                "YES_TCNT": "200",
                "NO_TCNT": "80",
                "BLANK_TCNT": "20",
                "PROC_RESULT_CD": "원안가결",
            }
        ]
        mock_client = _make_mock_client(sample_rows, "get_vote_results")

        with patch("data_go_mcp.open_assembly.server.AssemblyAPIClient", return_value=mock_client):
            result = await get_vote_results(age="22")

        assert result["count"] == 1
        assert result["votes"][0]["YES_TCNT"] == "200"
