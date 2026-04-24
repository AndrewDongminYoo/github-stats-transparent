# 깃허브 통계 시각화 : 투명

> 깃허브 사용자 및 저장소 통계를 GitHub Actions를 사용해 시각화합니다.

<a href="https://github.com/AndrewDongminYoo/github-stats-transparent">

![ ](https://raw.githubusercontent.com/AndrewDongminYoo/github-stats-transparent/refs/heads/output/generated/overview.svg)
![ ](https://raw.githubusercontent.com/AndrewDongminYoo/github-stats-transparent/refs/heads/output/generated/languages.svg)

</a>

> 참고: 이 저장소는 [jstrieb/github-stats](https://github.com/jstrieb/github-stats) 프로젝트의 확장판입니다.  
> 원본 프로젝트에서 분리된 포크 형태로, 이 저장소를 마음에 들어 하신다면 원본 프로젝트에도 스타를 남겨주세요.

## ⚠️ 주의사항

프로젝트는 읽기 권한이 있는 개인 액세스 토큰을 사용합니다. 일부 비공개 저장소를 읽을 때 오류가 발생하면 해당 예외가 워크플로 로그에 출력됩니다.  
이 예외 로그는 포크된 저장소의 Actions 탭에서 누구나 볼 수 있으므로, 일부 비공개 저장소 이름이 노출될 수 있습니다.

## ⚙️ 설치 방법

<!-- TODO: Add details and screenshots -->

1. [여기](https://docs.github.com/en/github/authenticating-to-github/creating-a-personal-access-token) 안내에 따라 `read:user`, `repo`, `user:email` 권한이 있는 개인 액세스 토큰을 생성하고, 생성된 토큰을 복사합니다.

2. [이 저장소 포크하기](https://github.com/AndrewDongminYoo/github-stats-transparent/fork)를 클릭해 저장소를 포크합니다.

3. 포크된 저장소의 "Settings" → "Secrets" 페이지(화면 왼쪽 하단)로 이동해, `ACCESS_TOKEN`이라는 이름으로 새 시크릿을 만들고 복사한 토큰을 붙여넣습니다.

   ![ ](https://raw.githubusercontent.com/AndrewDongminYoo/github-stats-transparent/main/readme_images/Actions.png)

4. 특정 저장소를 제외하고 싶다면, `EXCLUDED`라는 시크릿을 만들고 제외할 저장소 이름들을 쉼표로 구분해 입력합니다.

   <img src='https://raw.githubusercontent.com/AndrewDongminYoo/github-stats-transparent/main/readme_images/Exclude.png' height='250px'/>

5. 특정 언어를 제외하고 싶다면, `EXCLUDED_LANGS`라는 시크릿을 만들고 제외할 언어 이름들을 쉼표로 구분해 입력합니다.

6. 포크한 저장소의 통계도 포함하려면 `COUNT_STATS_FROM_FORKS`라는 시크릿을 생성하고, 아무 값이나 입력하면 됩니다.

   <img src='https://raw.githubusercontent.com/AndrewDongminYoo/github-stats-transparent/main/readme_images/Forks.png' height='250px'/>

7. [Actions 페이지](../../actions?query=workflow%3A"Generate+Stats+Images")에서 "Run Workflow" 버튼을 눌러 이미지를 처음 생성해봅니다. 이후 매시간 자동 생성되며, 수동으로도 다시 실행할 수 있습니다.

8. 생성된 이미지는 `output` 브랜치 내 [`generated`](../output/generated) 폴더에서 확인할 수 있습니다.

9. 다른 사람들이 통계 이미지를 생성할 수 있도록 이 저장소에 링크를 남겨주세요.

10. 도움이 되셨다면 Star를 눌러주세요!

<br>
<br>

## 🤔 왜 투명일까요 ??

GitHub의 다크 모드 도입으로 인해, 밝은 테마와 어두운 테마 모두에서 잘 어울리는 배경색을 찾기가 어려워졌습니다.  
이 문제를 해결하고자 가장 간단한 방법은 배경을 투명으로 유지하는 것이었고, 텍스트 색상은 밝은 배경과 어두운 배경 모두에서 가독성을 유지할 수 있도록 여러 값을 시도한 끝에 결정한 것입니다.

![ ](https://raw.githubusercontent.com/AndrewDongminYoo/github-stats-transparent/refs/heads/main/readme_images/light.png)

![ ](https://raw.githubusercontent.com/AndrewDongminYoo/github-stats-transparent/refs/heads/main/readme_images/dark.png)

## 관련 프로젝트

- [jstrieb/github-stats](https://github.com/jstrieb/github-stats) 포크의 확장판
- [anuraghazra/github-readme-stats](https://github.com/anuraghazra/github-readme-stats)을 개선하고자 하는 욕구에서 영감을 받음
- [GitHub Octicons](https://primer.style/octicons/)을 활용해 GitHub UI와 동일한 아이콘 사용
