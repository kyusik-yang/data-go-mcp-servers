# data-go-mcp.open-assembly

열린국회정보(open.assembly.go.kr) Open API MCP 서버 — 의안, 의원, 표결, 회의록, 청원 조회

## 설치 및 사용

### Claude Desktop 설정

```json
{
  "mcpServers": {
    "data-go-mcp.open-assembly": {
      "command": "uvx",
      "args": ["data-go-mcp.open-assembly@latest"],
      "env": {
        "ASSEMBLY_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

API 키는 [열린국회정보](https://open.assembly.go.kr) 회원가입 후 발급받을 수 있습니다.

## 제공 Tools (P1 — 엔드포인트 확인 완료)

| Tool | 설명 | 엔드포인트 |
|------|------|----------|
| `search_bills` | 국회의원 발의법률안 검색 | `nzmimeepazxkubdpn` |
| `get_bill_detail` | 의안 상세정보 조회 | `ALLBILL` |
| `get_member_info` | 국회의원 정보 조회 | `nwvrqwxyaytdsfvhu` |
| `get_vote_results` | 의안별 본회의 표결현황 | `ncocpgfiaoituanbr` |
| `get_bill_review` | 의안 처리·심사정보 | `nwbpacrgavhjryiph` |

## 제공 Tools (P2 — 엔드포인트 확인 필요)

| Tool | 설명 | 상태 |
|------|------|------|
| `search_minutes` | 회의록 검색 (위원회/본회의) | TODO: 엔드포인트 확인 필요 |
| `get_petitions` | 청원 접수목록 조회 | TODO: 엔드포인트 확인 필요 |
| `get_bill_content` | 법률안 제안이유 및 주요내용 | TODO: 엔드포인트 확인 필요 |
| `get_bill_proposers` | 의안 공동발의자 정보 | TODO: 엔드포인트 확인 필요 |
| `get_committee_members` | 위원회 위원 명단 | TODO: 엔드포인트 확인 필요 |

## 사용 예시

```
22대 국회에서 발의된 AI 관련 법률안을 찾아줘
더불어민주당 소속 의원 목록을 알려줘
반도체특별법 표결 결과를 보여줘
```

## 로컬 개발

```bash
cd src/open-assembly
cp .env.example .env
# .env에 ASSEMBLY_API_KEY 입력
uv sync --dev
uv run pytest tests/
```
