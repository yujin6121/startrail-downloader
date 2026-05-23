# STAR TRAIL Downloader

STAR TRAIL 사이트의 `download.txt`에 적힌 URL을 내려받는 간단한 다운로드 스크립트입니다.

보호된 이미지 URL은 브라우저 쿠키가 있어야 정상적으로 받을 수 있습니다.

## 준비

Python 3이 필요합니다.

```bash
python3 --version
```

## 쿠키 설정

프로젝트 루트에 `.env` 파일을 만들고, 브라우저 개발자 도구에서 복사한 Cookie 값을 넣습니다.

```bash
STARTRAIL_COOKIE='startrail_sid=...; startrail_progress=...'
```

`startrail_sid`와 `startrail_progress`는 STAR TRAIL 사이트를 브라우저에서 열고, 보호 이미지가 보이는 상태에서 요청 헤더의 `cookie` 값을 그대로 복사하면 됩니다.

예시:

```bash
STARTRAIL_COOKIE='startrail_sid=abcdef...; startrail_progress=eyJ...'
```

주의: `.env`에는 실제 쿠키가 들어가므로 공유하지 않는 것이 좋습니다.

## 실행

기본 실행:

```bash
./run_download.sh
```

위 명령은 내부적으로 다음을 실행합니다.

```bash
python3 download_images.py download.txt
```

## 다운로드 목록 수정

다운로드할 URL은 `download.txt`에 적습니다.

텍스트 중 URL만 자동으로 추출하므로, 아래처럼 설명과 URL을 섞어 써도 됩니다.

```text
- 배경음악
https://startrail.stellive.me/audio/bgm.mp3
```

## 저장 구조

기본적으로 `downloads` 폴더 아래에 종류별로 정리됩니다.

```text
downloads/
  yuni/
    wallpapers/
      yuni-1.jpg
    artworks/
      all-yuni.jpg
  hina/
    wallpapers/
      hina-1.jpg
  audio/
    bgm.mp3
  assets/
    main-star-bg.svg
```

같은 이름의 파일이 이미 있으면 `_1`, `_2`처럼 번호를 붙여 덮어쓰지 않습니다.

## 옵션

다른 입력 파일 사용:

```bash
python3 download_images.py other.txt
```

다른 출력 폴더 사용:

```bash
python3 download_images.py download.txt --outdir my_downloads
```

폴더 정리 없이 한 폴더에 저장:

```bash
python3 download_images.py download.txt --flat
```

쿠키를 명령어에서 직접 지정:

```bash
python3 download_images.py download.txt --cookie 'startrail_sid=...; startrail_progress=...'
```

재시도 횟수 지정:

```bash
python3 download_images.py download.txt --retries 3
```

## 오류 해결

`HTTP 404 Not Found`가 보호 이미지에서 발생하면 대부분 쿠키가 없거나 만료된 경우입니다.

1. 브라우저에서 STAR TRAIL 사이트를 다시 엽니다.
2. 보호 이미지가 보이는 상태인지 확인합니다.
3. 개발자 도구 Network 탭에서 요청 헤더의 `cookie` 값을 다시 복사합니다.
4. `.env`의 `STARTRAIL_COOKIE` 값을 새 값으로 교체합니다.
5. `./run_download.sh`를 다시 실행합니다.

다운로드 실패 내역은 `downloads/error_log.txt`에 기록됩니다.
# startrail-downloader
