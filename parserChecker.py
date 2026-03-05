from parser import ResumeParser, RESOURCE_DIR, POPPLER_PATH


def main():
    parsed = ResumeParser(
        r"data/Resume - Lokesh (1).pdf",
        RESOURCE_DIR,
        poppler_path=POPPLER_PATH,
    )
    print(parsed.data)


if __name__ == "__main__":
    main()