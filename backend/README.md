# Portal Shell - Backend

## 서비스 등록 규칙

서비스는 `POST /register`로 등록합니다. 등록 요청은 `metadata`와 `spec`으로
구분합니다.

```yaml
metadata:
  namespace: robotics
  name: mission-management
  version: 5.1.6

spec:
  description: A service to manage missions for robots.
  display:
    name: 미션 관리
    icon: file-lines
    order: 10
  frontend:
    type: iframe
    url: http://localhost:3001
  backend:
    healthUrl: http://localhost:8001/health
```

### 식별자

- 서비스는 `(metadata.namespace, metadata.name)` 조합으로 식별합니다.
- 같은 namespace에는 같은 name을 중복 등록할 수 없습니다.
- 다른 namespace에서는 같은 name을 사용할 수 있습니다.
- `namespace`와 `name`은 lowercase kebab-case 사용을 권장합니다.
- 등록 후 `namespace`와 `name`은 update API로 변경할 수 없습니다.

현재 kebab-case 형식은 애플리케이션에서 강제하지 않으므로 등록 주체가 규칙을
지켜야 합니다.

### Metadata

| 필드 | 필수 | 설명 |
| --- | --- | --- |
| `namespace` | 예 | 서비스 소유 팀 또는 조직의 영역 |
| `name` | 예 | namespace 내 서비스 식별자 |
| `version` | 예 | 등록된 서비스 버전. Semantic Versioning 권장 |

### Spec

| 필드 | 필수 | 설명 |
| --- | --- | --- |
| `description` | 예 | 서비스 설명 |
| `display.name` | 예 | 포털에 표시할 이름 |
| `display.icon` | 예 | 포털에 표시할 아이콘 식별자 |
| `display.order` | 아니요 | 표시 순서. 기본값 `10` |
| `frontend.type` | 예 | UI 통합 방식. 예: `iframe` |
| `frontend.url` | 예 | 프론트엔드 URL |
| `backend.healthUrl` | 예 | Registry의 상태 확인에 사용할 health endpoint |

`healthUrl`은 JSON/YAML API에서는 lowerCamelCase를 사용하고 Python 내부에서는
`health_url`로 처리합니다.

Registry는 `healthUrl`을 주기적으로 호출합니다. HTTP `2xx` 응답은 성공이며,
연속 실패 횟수가 임계값에 도달하면 상태를 `unhealthy`로 변경합니다. 이후 한 번의
성공으로 다시 `healthy` 상태가 됩니다.

### 등록 응답

최초 등록은 `201 Created`와 Registry 내부 ID를 반환합니다.

```json
{
  "id": 1,
  "metadata": {
    "namespace": "robotics",
    "name": "mission-management",
    "version": "5.1.6"
  },
  "spec": {
    "description": "A service to manage missions for robots.",
    "display": {
      "name": "미션 관리",
      "icon": "file-lines",
      "order": 10
    },
    "frontend": {
      "type": "iframe",
      "url": "http://localhost:3001"
    },
    "backend": {
      "healthUrl": "http://localhost:8001/health"
    }
  },
  "status": {
    "health": {
      "state": "unknown",
      "checkedAt": null,
      "lastHealthyAt": null,
      "consecutiveFailures": 0,
      "error": null
    }
  }
}
```

현재 등록 API는 idempotent upsert가 아닙니다. 동일한 `(namespace, name)`을 다시
등록하면 `409 Conflict`를 반환합니다.

```json
{
  "code": "REG-1001",
  "detail": "Service already registered: robotics/mission-management"
}
```

### 관련 API

| Method | Path | 설명 |
| --- | --- | --- |
| `POST` | `/register` | 서비스 등록 |
| `GET` | `/services` | 전체 서비스 조회 |
| `GET` | `/services/{namespace}/{name}` | 서비스 단건 조회 |
| `POST` | `/services/{namespace}/{name}/update` | version 또는 spec 일부 수정 |
| `POST` | `/services/{namespace}/{name}/delete` | 서비스 삭제 |

## Health Check 설정

| 환경변수 | 기본값 | 설명 |
| --- | --- | --- |
| `HEALTH_CHECK_INTERVAL_SECONDS` | `30` | polling 기본 간격 |
| `HEALTH_CHECK_TIMEOUT_SECONDS` | `3` | 요청 timeout |
| `HEALTH_CHECK_FAILURE_THRESHOLD` | `3` | unhealthy 전환 연속 실패 횟수 |
| `HEALTH_CHECK_MAX_CONCURRENCY` | `10` | 동시 요청 상한 |
| `HEALTH_CHECK_JITTER_RATIO` | `0.2` | polling 간격 jitter 비율 |

상태는 `unknown`, `healthy`, `unhealthy` 중 하나입니다. `healthUrl`이 변경되면
상태와 실패 횟수를 초기화합니다. redirect는 따라가지 않으며 `http`와 `https`
URL만 등록할 수 있습니다.

현재 health checker는 FastAPI 프로세스의 background task로 동작합니다. 여러
Uvicorn worker나 여러 replica를 실행하면 중복 polling되므로 현재 구성에서는
single worker로 실행해야 합니다.
