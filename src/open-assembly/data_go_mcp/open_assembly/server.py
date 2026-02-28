"""MCP server for Korean National Assembly Open API (open.assembly.go.kr)."""

import os
import sys
import logging
from typing import Any, Optional

from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

from .client import AssemblyAPIClient

load_dotenv()

mcp = FastMCP("Korean National Assembly Open API")

UNIT_CD_MAP = {
    "22": "100022",
    "21": "100021",
    "20": "100020",
    "19": "100019",
    "18": "100018",
}


def _unit_cd(age: str) -> str:
    """대수 문자열을 UNIT_CD로 변환."""
    return UNIT_CD_MAP.get(age, f"1000{age}")


# ------------------------------------------------------------------
# P1 Tools
# ------------------------------------------------------------------


@mcp.tool()
async def search_bills(
    age: str,
    bill_name: Optional[str] = None,
    proposer: Optional[str] = None,
    proc_result: Optional[str] = None,
    committee: Optional[str] = None,
    page: int = 1,
    page_size: int = 10,
) -> dict[str, Any]:
    """
    국회의원 발의법률안을 검색합니다.

    Search for member-sponsored bills in the National Assembly.

    Args:
        age: 대수 (예: "22" = 22대 국회) — 필수
        bill_name: 법률안명 키워드 (선택)
        proposer: 대표발의자명 (선택)
        proc_result: 처리결과 필터 — "원안가결" | "수정가결" | "부결" | "폐기" (선택)
        committee: 소관위원회명 (선택)
        page: 페이지 번호 (기본값: 1)
        page_size: 페이지당 결과수 (기본값: 10, 최대: 100)

    Returns:
        bills: 법률안 목록 (BILL_ID, BILL_NO, BILL_NAME, RST_PROPOSER, PUBL_PROPOSER,
               PROPOSE_DT, PROC_RESULT, COMMITTEE, DETAIL_LINK 등)
        count: 반환된 건수
    """
    async with AssemblyAPIClient() as client:
        try:
            rows = await client.search_bills(
                age=age,
                bill_name=bill_name,
                proposer=proposer,
                proc_result=proc_result,
                committee=committee,
                page=page,
                page_size=page_size,
            )
            return {
                "bills": rows,
                "count": len(rows),
                "message": f"{len(rows)}건의 법률안을 찾았습니다." if rows else "검색 결과가 없습니다.",
            }
        except Exception as e:
            return {"error": str(e), "bills": [], "count": 0}


@mcp.tool()
async def get_bill_detail(bill_no: str) -> dict[str, Any]:
    """
    의안 상세정보를 조회합니다 (의안정보 통합 API).

    Get comprehensive bill information including processing history.

    Args:
        bill_no: 의안번호 (예: "2217175") — 필수. search_bills 결과의 BILL_NO 사용.

    Returns:
        bill: 의안 상세정보 (BILL_NO, BILL_NM, BILL_KND, PPSR_NM, PPSL_DT,
              위원회 심사일정, 본회의 처리일정, 공포 정보, LINK_URL 등)
    """
    async with AssemblyAPIClient() as client:
        try:
            rows = await client.get_bill_detail(bill_no=bill_no)
            if not rows:
                return {"bill": None, "message": f"의안번호 {bill_no}를 찾을 수 없습니다."}
            return {"bill": rows[0], "message": "조회 성공"}
        except Exception as e:
            return {"error": str(e), "bill": None}


@mcp.tool()
async def get_member_info(
    age: str = "22",
    name: Optional[str] = None,
    party: Optional[str] = None,
    district: Optional[str] = None,
    committee: Optional[str] = None,
    page: int = 1,
    page_size: int = 10,
) -> dict[str, Any]:
    """
    국회의원 정보를 조회합니다.

    Query National Assembly member information.

    Args:
        age: 대수 (예: "22" = 22대, "21" = 21대) (기본값: "22")
        name: 의원 한글명 (선택, 예: "홍길동")
        party: 정당명 (선택, 예: "더불어민주당", "국민의힘")
        district: 선거구명 (선택, 예: "서울 강남갑", "비례대표")
        committee: 소속위원회명 (선택, 예: "법제사법위원회")
        page: 페이지 번호 (기본값: 1)
        page_size: 페이지당 결과수 (기본값: 10)

    Returns:
        members: 의원 목록 (HG_NM, POLY_NM, ORIG_NM, CMIT_NM, REELE_GBN_NM,
                 SEX_GBN_NM, TEL_NO, E_MAIL, HOMEPAGE, MONA_CD, ASSEM_ADDR 등)
        count: 반환된 건수
    """
    async with AssemblyAPIClient() as client:
        try:
            rows = await client.get_member_info(
                unit_cd=_unit_cd(age),
                name=name,
                party=party,
                district=district,
                committee=committee,
                page=page,
                page_size=page_size,
            )
            return {
                "members": rows,
                "count": len(rows),
                "message": f"{len(rows)}명의 의원 정보를 찾았습니다." if rows else "검색 결과가 없습니다.",
            }
        except Exception as e:
            return {"error": str(e), "members": [], "count": 0}


@mcp.tool()
async def get_vote_results(
    age: str,
    bill_no: Optional[str] = None,
    bill_name: Optional[str] = None,
    page: int = 1,
    page_size: int = 10,
) -> dict[str, Any]:
    """
    의안별 본회의 표결현황을 조회합니다.

    Get plenary vote results by bill (aggregate counts: yes/no/abstain).

    Args:
        age: 대수 (예: "22") — 필수
        bill_no: 의안번호로 필터 (선택)
        bill_name: 의안명 키워드로 필터 (선택)
        page: 페이지 번호 (기본값: 1)
        page_size: 페이지당 결과수 (기본값: 10)

    Returns:
        votes: 표결 목록 (BILL_NO, BILL_NAME, PROC_DT, MEMBER_TCNT,
               VOTE_TCNT, YES_TCNT, NO_TCNT, BLANK_TCNT, PROC_RESULT_CD, LINK_URL 등)
        count: 반환된 건수
    """
    async with AssemblyAPIClient() as client:
        try:
            rows = await client.get_vote_results(
                age=age,
                bill_no=bill_no,
                bill_name=bill_name,
                page=page,
                page_size=page_size,
            )
            return {
                "votes": rows,
                "count": len(rows),
                "message": f"{len(rows)}건의 표결 결과를 찾았습니다." if rows else "검색 결과가 없습니다.",
            }
        except Exception as e:
            return {"error": str(e), "votes": [], "count": 0}


@mcp.tool()
async def get_bill_review(
    age: str,
    bill_no: Optional[str] = None,
    committee: Optional[str] = None,
    page: int = 1,
    page_size: int = 10,
) -> dict[str, Any]:
    """
    의안 처리·심사정보를 조회합니다 (위원회 및 본회의 처리 경로).

    Get bill review and processing information (committee + plenary timeline).

    Args:
        age: 대수 (예: "22") — 필수
        bill_no: 의안번호 (선택)
        committee: 위원회명으로 필터 (선택)
        page: 페이지 번호 (기본값: 1)
        page_size: 페이지당 결과수 (기본값: 10)

    Returns:
        reviews: 심사정보 목록 (BILL_NO, BILL_NM, COMMITTEE_NM, PROC_RESULT_CD,
                 위원회 및 본회의 처리 일정, 표결 결과 등)
        count: 반환된 건수
    """
    async with AssemblyAPIClient() as client:
        try:
            rows = await client.get_bill_review(
                age=age,
                bill_no=bill_no,
                committee=committee,
                page=page,
                page_size=page_size,
            )
            return {
                "reviews": rows,
                "count": len(rows),
                "message": f"{len(rows)}건의 심사정보를 찾았습니다." if rows else "검색 결과가 없습니다.",
            }
        except Exception as e:
            return {"error": str(e), "reviews": [], "count": 0}


# ------------------------------------------------------------------
# P2 Tools (엔드포인트 확인 후 활성화)
# ------------------------------------------------------------------


@mcp.tool()
async def search_minutes(
    age: Optional[str] = None,
    committee: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    minutes_type: str = "committee",
    page: int = 1,
    page_size: int = 10,
) -> dict[str, Any]:
    """
    국회 회의록을 검색합니다 (위원회 또는 본회의).

    Search National Assembly meeting minutes.

    NOTE: 이 tool은 엔드포인트 코드 확인 후 활성화됩니다.
    client.py의 EP_MINUTES_COMMITTEE / EP_MINUTES_PLENARY를 업데이트하세요.
    infaId: OR137O001023MZ19321 (위원회), OO1X9P001017YF13038 (본회의)

    Args:
        age: 대수 (선택)
        committee: 위원회명 (선택, minutes_type="committee"일 때)
        date_from: 시작일 (선택, YYYYMMDD)
        date_to: 종료일 (선택, YYYYMMDD)
        minutes_type: "committee" (위원회) | "plenary" (본회의) (기본값: "committee")
        page: 페이지 번호 (기본값: 1)
        page_size: 페이지당 결과수 (기본값: 10)
    """
    async with AssemblyAPIClient() as client:
        try:
            rows = await client.search_minutes(
                age=age,
                committee=committee,
                date_from=date_from,
                date_to=date_to,
                page=page,
                page_size=page_size,
                minutes_type=minutes_type,
            )
            return {
                "minutes": rows,
                "count": len(rows),
                "message": f"{len(rows)}건의 회의록을 찾았습니다." if rows else "검색 결과가 없습니다.",
            }
        except Exception as e:
            return {"error": str(e), "minutes": [], "count": 0}


@mcp.tool()
async def get_petitions(
    status: Optional[str] = None,
    keyword: Optional[str] = None,
    page: int = 1,
    page_size: int = 10,
) -> dict[str, Any]:
    """
    청원 접수목록을 조회합니다.

    Get list of petitions filed to the National Assembly.

    NOTE: 이 tool은 엔드포인트 코드 확인 후 활성화됩니다.
    client.py의 EP_PETITION을 업데이트하세요.
    infaId: OOWY4R001216HX11482

    Args:
        status: 청원 상태 필터 (선택)
        keyword: 키워드 검색 (선택)
        page: 페이지 번호 (기본값: 1)
        page_size: 페이지당 결과수 (기본값: 10)
    """
    async with AssemblyAPIClient() as client:
        try:
            rows = await client.get_petitions(
                status=status,
                keyword=keyword,
                page=page,
                page_size=page_size,
            )
            return {
                "petitions": rows,
                "count": len(rows),
                "message": f"{len(rows)}건의 청원을 찾았습니다." if rows else "검색 결과가 없습니다.",
            }
        except Exception as e:
            return {"error": str(e), "petitions": [], "count": 0}


@mcp.tool()
async def get_bill_content(bill_id: str) -> dict[str, Any]:
    """
    법률안 제안이유 및 주요내용을 조회합니다.

    Get the rationale and key content of a bill.

    NOTE: 이 tool은 엔드포인트 코드 확인 후 활성화됩니다.
    client.py의 EP_BILL_CONTENT를 업데이트하세요.
    infaId: OS46YD0012559515463

    Args:
        bill_id: 의안ID (search_bills 결과의 BILL_ID) — 필수
    """
    async with AssemblyAPIClient() as client:
        try:
            rows = await client.get_bill_content(bill_id=bill_id)
            if not rows:
                return {"content": None, "message": f"BILL_ID {bill_id}의 내용을 찾을 수 없습니다."}
            return {"content": rows[0], "message": "조회 성공"}
        except Exception as e:
            return {"error": str(e), "content": None}


@mcp.tool()
async def get_bill_proposers(bill_no: str) -> dict[str, Any]:
    """
    의안 제안자(공동발의자) 정보를 조회합니다.

    Get the list of co-sponsors for a bill.

    NOTE: 이 tool은 엔드포인트 코드 확인 후 활성화됩니다.
    client.py의 EP_BILL_PROPOSERS를 업데이트하세요.
    infaId: OOWY4R001216HX11460

    Args:
        bill_no: 의안번호 (예: "2217175") — 필수
    """
    async with AssemblyAPIClient() as client:
        try:
            rows = await client.get_bill_proposers(bill_no=bill_no)
            return {
                "proposers": rows,
                "count": len(rows),
                "message": f"{len(rows)}명의 제안자 정보를 찾았습니다." if rows else "검색 결과가 없습니다.",
            }
        except Exception as e:
            return {"error": str(e), "proposers": [], "count": 0}


@mcp.tool()
async def get_committee_members(
    age: str = "22",
    committee: Optional[str] = None,
    page: int = 1,
    page_size: int = 50,
) -> dict[str, Any]:
    """
    위원회 위원 명단을 조회합니다.

    Get the list of members for a specific committee.

    NOTE: 이 tool은 엔드포인트 코드 확인 후 활성화됩니다.
    client.py의 EP_COMMITTEE_MEMBERS를 업데이트하세요.
    infaId: OCAJQ4001000LI18751

    Args:
        age: 대수 (기본값: "22")
        committee: 위원회명 (선택, 예: "법제사법위원회")
        page: 페이지 번호 (기본값: 1)
        page_size: 페이지당 결과수 (기본값: 50)
    """
    async with AssemblyAPIClient() as client:
        try:
            rows = await client.get_committee_members(
                unit_cd=_unit_cd(age),
                committee=committee,
                page=page,
                page_size=page_size,
            )
            return {
                "members": rows,
                "count": len(rows),
                "message": f"{len(rows)}명의 위원 명단을 찾았습니다." if rows else "검색 결과가 없습니다.",
            }
        except Exception as e:
            return {"error": str(e), "members": [], "count": 0}


# ------------------------------------------------------------------
# Entry point
# ------------------------------------------------------------------


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    api_key = os.getenv("ASSEMBLY_API_KEY")
    if not api_key:
        logging.error("ASSEMBLY_API_KEY environment variable is not set.")
        logging.error("Sign up at https://open.assembly.go.kr to get your API key.")
        sys.exit(1)
    mcp.run()


if __name__ == "__main__":
    main()
