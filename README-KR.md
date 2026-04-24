# github-stats-transparent

[English README](README.md)

기본 설정에서는 GitHub Actions가 생성 결과를 `output` 브랜치로 푸시하고, 필요하면 로컬에서 `generated/` 디렉터리로도 생성할 수 있는 투명 배경 GitHub 통계 카드입니다.

이 포크는 `rahul-jha98/github-stats-transparent`에서 시작했지만, 지금은 `Lines of code changed` 문제를 해결하는 데 초점을 맞추고 있습니다. 이를 위해 `jstrieb/github-stats`의 관련 Zig 동작을 Python으로 다시 구현했습니다.

## 이 프로젝트가 하는 일

이 저장소는 투명한 SVG 통계 카드를 생성합니다.

- 별, 포크, 기여 수, 저장소 수, 조회 수, `Lines of code changed`를 보여주는 overview 카드
- 수집된 저장소 기준으로 언어 비율을 보여주는 languages 카드

기본 설정에서는 GitHub Actions가 카드를 생성한 뒤 `output` 브랜치의 `generated/` 디렉터리로 푸시하며, 프로필 README나 다른 Markdown 문서에 그대로 임베드할 수 있습니다. 로컬에서 실행하면 동일한 결과물이 현재 작업 디렉터리의 `generated/` 아래에 생성됩니다.

## 왜 이 포크가 필요한가

원본 투명 포크는 카드 디자인과 사용 방식은 유지하고 있었지만, 오래된 Python 구현이 갖고 있던 `Lines of code changed` 정확도 문제도 함께 가져오고 있었습니다.

문제의 핵심은 overview 카드에 표시되는 이 값이 저장소 통계 API 상태에 따라 0으로 떨어지거나 실제보다 적게 계산될 수 있었다는 점입니다. 특히 GitHub가 contributor stats 계산을 늦게 끝내는 저장소에서는 이 현상이 더 자주 나타났습니다.

이 포크의 목적은 투명 카드라는 장점은 그대로 유지하면서, 해당 통계를 Python 쪽에서 더 견고하게 계산하도록 바꾸는 것입니다.

## 기존 투명 Python 포크에서 무엇이 문제였나

이전 구현은 GitHub REST API의 contributor stats 엔드포인트에 지나치게 의존했습니다.

- `/repos/{owner}/{repo}/stats/contributors`는 GitHub가 통계를 아직 계산 중이면 `202 Accepted`를 반환할 수 있습니다.
- 규모가 큰 저장소나 활동이 많은 저장소는 `202`가 오래 지속될 수 있습니다.
- API에서 바로 쓸 수 있는 데이터가 오지 않을 때, 기존 Python 구현에는 upstream Zig 버전 수준의 복구 경로가 없었습니다.

결과적으로 `Lines of code changed`는 카드에서 가장 신뢰하기 어려운 숫자가 되기 쉬웠습니다.

## 이 포크가 `Lines of code changed`를 고치는 방법

이 포크는 `jstrieb/github-stats`의 핵심 복구 전략을 Python으로 옮겼습니다.

1. 저장소 stats 엔드포인트가 `202 Accepted`를 반환하면 짧은 랜덤 대기 후 여러 번 다시 시도합니다.
2. 그래도 유효한 데이터를 받지 못하거나, 재시도 성격의 실패인 `403` 또는 `429`가 나오면 git 기반 계산으로 넘어갑니다.
3. git fallback은 저장소를 가벼운 bare clone 형태로 가져온 뒤 `git log --numstat`를 실행하고, 인증된 사용자의 contributor email과 일치하는 커밋만 합산합니다.
4. 토큰으로 이메일 목록을 가져오지 못하면 마지막 수단으로 GitHub noreply 주소를 사용합니다.

이것이 이 포크의 핵심 수정 사항입니다. 즉, 투명 Python 버전이 이제 `Lines of code changed`에 대해 upstream Zig 버전과 같은 방향의 복구 전략을 따릅니다.

또한 워크플로 로그에서는 저장소별 상세 오류 출력을 억제하고, 주된 요약 출력으로 아래 형태의 sanitize된 한 줄 요약을 남깁니다.

`Lines changed sources: API X | git fallback Y | failed Z`

즉, 로그는 디버깅에 필요한 최소한의 정보는 유지하면서도 과도한 상세 출력은 피하도록 정리되어 있습니다.

## Setup

### GitHub Actions 기준

1. personal access token을 만듭니다.
2. 권장 권한은 다음과 같습니다.
   - `read:user`
   - private repository 통계를 포함하려면 `repo`
   - git fallback에서 전체 이메일 목록 기준으로 더 잘 매칭하려면 `user:email`
3. 포크한 저장소 또는 사용하는 저장소의 Secrets에 `ACCESS_TOKEN` 이름으로 등록합니다.
4. 필요하면 아래 설정 변수도 함께 추가합니다.
5. Actions 탭에서 `Generate Stats Images` 워크플로를 한 번 수동 실행합니다.
6. 이후 생성된 카드는 `output` 브랜치의 `generated/` 아래에서 사용할 수 있습니다.

기본 스케줄 실행도 설정되어 있으므로, 한 번만 초기 실행해 두면 이후 갱신 흐름을 확인하기 쉽습니다.

### 로컬에서 실행하는 경우

1. 의존성을 설치합니다.

```bash
python3 -m pip install -r requirements.txt
```

2. 토큰만 지정해서 실행해도 됩니다. 로컬에서 `GITHUB_ACTOR`를 비워 두면 스크립트가 인증된 viewer 기준으로 로그인 이름을 조회합니다.

```bash
ACCESS_TOKEN=your_token_here python3 generate_images.py
```

로컬 실행에서는 `git`이 설치되어 있어야 합니다. `Lines of code changed` 보정 로직이 필요할 때 git fallback이 실제로 동작해야 하기 때문입니다.

## 토큰 권한

이 포크는 personal access token 사용을 권장하지만, 모든 권한이 모든 상황에서 반드시 필요한 것은 아닙니다.

- `read:user`: 사용자 프로필 및 기본 사용자 데이터 조회를 위한 권장 기본 권한
- `repo`: private repository와 그 통계를 포함하려는 경우 필요
- `user:email`: git fallback에서 contributor email 목록을 조회할 수 있어 매칭 정확도가 좋아지지만, `/user/emails`를 읽지 못해도 코드는 GitHub noreply 주소로 fallback할 수 있음

코드상으로는 `ACCESS_TOKEN`이 없을 때 `GITHUB_TOKEN`으로 넘어갈 수도 있지만, 이 포크를 안정적으로 운영하려면 personal access token 구성이 가장 적합합니다.

## 설정 옵션

| 변수 | 필수 여부 | 설명 |
| --- | --- | --- |
| `ACCESS_TOKEN` | 안정적인 사용을 위해 권장 | API 요청과 git fallback 인증에 사용하는 personal access token |
| `EXCLUDED` | 선택 | 제외할 저장소 이름을 쉼표로 구분해 지정 |
| `EXCLUDED_LANGS` | 선택 | languages 카드에서 제외할 언어 이름을 쉼표로 구분해 지정 |
| `COUNT_STATS_FROM_FORKS` | 선택 | 비어 있지 않은 값이면 이 포크의 기존 통계 수집 흐름에서 더 넓은 저장소 집합을 포함 |
| `GITHUB_ACTOR` | Actions에서는 자동 제공, 로컬에서는 선택 | 로컬 실행 시 GitHub 로그인 이름을 직접 지정하는 override 값. 비워 두면 인증된 viewer 기준으로 자동 조회 |

## 제한 사항과 기대 동작

- `Lines of code changed`는 기존 투명 Python 포크보다 훨씬 신뢰할 수 있지만, 여전히 GitHub API 상태와 저장소 clone 가능 여부의 영향을 받습니다.
- API와 git fallback이 모두 실패한 저장소는 로그 요약에서 `failed`로 집계되며 최종 합계에는 `0`으로 반영됩니다.
- 토큰으로 이메일 목록을 읽지 못하면 GitHub noreply 주소를 사용하므로, 다른 이메일로 작성된 커밋은 누락될 수 있습니다.
- `views` 값은 GitHub traffic API가 제공하는 최근 기간 데이터 기준이며, 전체 누적 조회 수가 아닙니다.
- 저장소 수가 많거나 큰 저장소가 많으면 재시도와 git fallback 때문에 실행 시간이 늘어날 수 있습니다.

## Contributing

이슈와 풀 리퀘스트를 환영합니다.

특히 아래와 같은 기여는 매우 유용합니다.

- 통계 정확도 개선
- 실행 시간 또는 API 효율 개선
- 문서 개선
- GitHub API 동작 변화에 대한 호환성 수정

`Lines of code changed`가 아직도 어긋나는 사례를 발견하면 재현 정보와 함께 이슈를 남겨 주세요. 수정 방향이 명확하다면 바로 풀 리퀘스트를 보내 주셔도 좋습니다.
