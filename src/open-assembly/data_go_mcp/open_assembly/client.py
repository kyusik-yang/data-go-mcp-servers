"""API client for Korean National Assembly Open API (open.assembly.go.kr)."""

import os
from typing import Any, Optional

import httpx
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://open.assembly.go.kr/portal/openapi"

# Confirmed endpoint codes (verified 2026-02)
EP_BILLS = "nzmimeepazxkubdpn"          # 국회의원 발의법률안
EP_BILL_DETAIL = "ALLBILL"              # 의안정보 통합 API
EP_BILL_REVIEW = "nwbpacrgavhjryiph"    # 의안 처리·심사정보
EP_MEMBER = "nwvrqwxyaytdsfvhu"         # 국회의원 정보 통합 API
EP_VOTE = "ncocpgfiaoituanbr"           # 의안별 표결현황

# TODO: verify these endpoint codes via open.assembly.go.kr spec download
EP_MINUTES_COMMITTEE = "PLACEHOLDER_COMMITTEE_MINUTES"   # 위원회 회의록 (infaId: OR137O001023MZ19321)
EP_MINUTES_PLENARY = "PLACEHOLDER_PLENARY_MINUTES"       # 본회의 회의록 (infaId: OO1X9P001017YF13038)
EP_PETITION = "PLACEHOLDER_PETITION"                     # 청원 접수목록 (infaId: OOWY4R001216HX11482)
EP_BILL_CONTENT = "PLACEHOLDER_BILL_CONTENT"             # 법률안 제안이유 (infaId: OS46YD0012559515463)
EP_BILL_PROPOSERS = "PLACEHOLDER_BILL_PROPOSERS"         # 의안 제안자정보 (infaId: OOWY4R001216HX11460)
EP_COMMITTEE_MEMBERS = "PLACEHOLDER_COMMITTEE_MEMBERS"   # 위원회 위원 명단 (infaId: OCAJQ4001000LI18751)


class AssemblyAPIClient:
    """열린국회정보 Open API 클라이언트."""

    def __init__(self) -> None:
        self.api_key = os.getenv("ASSEMBLY_API_KEY")
        if not self.api_key:
            raise ValueError(
                "ASSEMBLY_API_KEY environment variable is required. "
                "Sign up at https://open.assembly.go.kr to get your API key."
            )
        self.client = httpx.AsyncClient(timeout=30.0)

    async def __aenter__(self) -> "AssemblyAPIClient":
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.client.aclose()

    def _base_params(self) -> dict[str, Any]:
        return {"KEY": self.api_key, "Type": "json"}

    def _parse_response(self, data: dict, endpoint: str) -> list[dict]:
        """열린국회 API 응답 파싱. INFO-200 = 빈 결과, INFO-000 = 정상."""
        body = data.get(endpoint, [])
        if not body:
            raise ValueError(f"Unexpected response structure for endpoint '{endpoint}'")

        head = body[0].get("head", [])
        result = head[1].get("RESULT", {}) if len(head) > 1 else {}
        code = result.get("CODE", "")

        if code == "INFO-200":
            return []
        if code != "INFO-000":
            msg = result.get("MESSAGE", "Unknown API error")
            raise ValueError(f"API error {code}: {msg}")

        rows = body[1].get("row", []) if len(body) > 1 else []
        # 단건이면 dict, 다건이면 list
        return rows if isinstance(rows, list) else [rows]

    async def _get(self, endpoint: str, params: dict[str, Any]) -> list[dict]:
        """GET 요청 실행 및 응답 파싱."""
        merged = {**self._base_params(), **{k: v for k, v in params.items() if v is not None}}
        url = f"{BASE_URL}/{endpoint}"
        try:
            resp = await self.client.get(url, params=merged)
            resp.raise_for_status()
            return self._parse_response(resp.json(), endpoint)
        except httpx.HTTPStatusError as e:
            raise ValueError(f"HTTP {e.response.status_code}: {e.response.text}") from e
        except ValueError:
            raise
        except Exception as e:
            raise ValueError(f"Request failed: {e}") from e

    # ------------------------------------------------------------------
    # P1: 핵심 6개 Tool 메서드
    # ------------------------------------------------------------------

    async def search_bills(
        self,
        age: str,
        bill_name: Optional[str] = None,
        proposer: Optional[str] = None,
        proc_result: Optional[str] = None,
        committee: Optional[str] = None,
        page: int = 1,
        page_size: int = 10,
    ) -> list[dict]:
        """국회의원 발의법률안 목록 조회."""
        return await self._get(EP_BILLS, {
            "AGE": age,
            "BILL_NAME": bill_name,
            "PROPOSER": proposer,
            "PROC_RESULT": proc_result,
            "COMMITTEE": committee,
            "pIndex": page,
            "pSize": page_size,
        })

    async def get_bill_detail(self, bill_no: str) -> list[dict]:
        """의안 상세정보 조회 (의안정보 통합 API)."""
        return await self._get(EP_BILL_DETAIL, {"BILL_NO": bill_no})

    async def get_member_info(
        self,
        unit_cd: str = "100022",
        name: Optional[str] = None,
        party: Optional[str] = None,
        district: Optional[str] = None,
        committee: Optional[str] = None,
        page: int = 1,
        page_size: int = 10,
    ) -> list[dict]:
        """국회의원 정보 조회."""
        return await self._get(EP_MEMBER, {
            "UNIT_CD": unit_cd,
            "HG_NM": name,
            "POLY_NM": party,
            "ORIG_NM": district,
            "CMIT_NM": committee,
            "pIndex": page,
            "pSize": page_size,
        })

    async def get_vote_results(
        self,
        age: str,
        bill_no: Optional[str] = None,
        bill_name: Optional[str] = None,
        page: int = 1,
        page_size: int = 10,
    ) -> list[dict]:
        """의안별 본회의 표결현황 조회."""
        return await self._get(EP_VOTE, {
            "AGE": age,
            "BILL_NO": bill_no,
            "BILL_NAME": bill_name,
            "pIndex": page,
            "pSize": page_size,
        })

    async def get_bill_review(
        self,
        age: str,
        bill_no: Optional[str] = None,
        committee: Optional[str] = None,
        page: int = 1,
        page_size: int = 10,
    ) -> list[dict]:
        """의안 처리·심사정보 조회 (위원회 및 본회의 처리 경로)."""
        return await self._get(EP_BILL_REVIEW, {
            "AGE": age,
            "BILL_NO": bill_no,
            "COMMITTEE_NM": committee,
            "pIndex": page,
            "pSize": page_size,
        })

    # ------------------------------------------------------------------
    # P2: 추가 4개 Tool 메서드 (엔드포인트 확인 필요)
    # ------------------------------------------------------------------

    async def search_minutes(
        self,
        age: Optional[str] = None,
        committee: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        page: int = 1,
        page_size: int = 10,
        minutes_type: str = "committee",
    ) -> list[dict]:
        """회의록 검색 (위원회 또는 본회의).

        TODO: EP_MINUTES_COMMITTEE, EP_MINUTES_PLENARY 엔드포인트 코드 확인 필요.
        open.assembly.go.kr에서 infaId OR137O001023MZ19321 (위원회)
        또는 OO1X9P001017YF13038 (본회의)의 명세서를 다운로드하여 확인.
        """
        ep = EP_MINUTES_COMMITTEE if minutes_type == "committee" else EP_MINUTES_PLENARY
        return await self._get(ep, {
            "AGE": age,
            "CMIT_NM": committee,
            "FROM_DATE": date_from,
            "TO_DATE": date_to,
            "pIndex": page,
            "pSize": page_size,
        })

    async def get_petitions(
        self,
        status: Optional[str] = None,
        keyword: Optional[str] = None,
        page: int = 1,
        page_size: int = 10,
    ) -> list[dict]:
        """청원 접수목록 조회.

        TODO: EP_PETITION 엔드포인트 코드 확인 필요.
        infaId: OOWY4R001216HX11482
        """
        return await self._get(EP_PETITION, {
            "STATUS": status,
            "KEYWORD": keyword,
            "pIndex": page,
            "pSize": page_size,
        })

    async def get_bill_content(self, bill_id: str) -> list[dict]:
        """법률안 제안이유 및 주요내용 조회.

        TODO: EP_BILL_CONTENT 엔드포인트 코드 확인 필요.
        infaId: OS46YD0012559515463
        """
        return await self._get(EP_BILL_CONTENT, {"BILL_ID": bill_id})

    async def get_bill_proposers(self, bill_no: str) -> list[dict]:
        """의안 제안자(공동발의자) 정보 조회.

        TODO: EP_BILL_PROPOSERS 엔드포인트 코드 확인 필요.
        infaId: OOWY4R001216HX11460
        """
        return await self._get(EP_BILL_PROPOSERS, {"BILL_NO": bill_no})

    async def get_committee_members(
        self,
        unit_cd: str = "100022",
        committee: Optional[str] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> list[dict]:
        """위원회 위원 명단 조회.

        TODO: EP_COMMITTEE_MEMBERS 엔드포인트 코드 확인 필요.
        infaId: OCAJQ4001000LI18751
        """
        return await self._get(EP_COMMITTEE_MEMBERS, {
            "UNIT_CD": unit_cd,
            "CMIT_NM": committee,
            "pIndex": page,
            "pSize": page_size,
        })
