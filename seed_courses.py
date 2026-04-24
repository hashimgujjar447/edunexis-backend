from courses.models.course import Course
from courses.models.section import Section
from courses.models.lesson import Lesson
from courses.models.attachment import Attachment


def run():
    course_data = {
        "Python for Beginners": [
            {
                "section_title": "Introduction to Python",
                "lessons": [
                    {
                        "title": "Welcome to Course",
                        "content": "Welcome to Python course.",
                        "video": "lessons/videos/welcome.mp4",
                        "attachments": [
                            {"title": "Intro PDF", "url": "https://example.com/intro"}
                        ]
                    },
                    {
                        "title": "What is Python",
                        "content": "Python is a programming language.",
                        "video": "",
                        "attachments": []
                    },
                ]
            },
            {
                "section_title": "Python Basics",
                "lessons": [
                    {
                        "title": "Variables",
                        "content": "Variables store data.",
                        "video": "",
                        "attachments": []
                    },
                    {
                        "title": "Data Types",
                        "content": "Different data types in Python.",
                        "video": "",
                        "attachments": []
                    },
                ]
            }
        ],

        "React - The Complete Guide": [
            {
                "section_title": "React Basics",
                "lessons": [
                    {
                        "title": "Intro to React",
                        "content": "React is a JS library.",
                        "video": "",
                        "attachments": []
                    }
                ]
            }
        ],

        "UI/UX Design Fundamentals": [
            {
                "section_title": "Design Basics",
                "lessons": [
                    {
                        "title": "What is UI/UX",
                        "content": "UI/UX explanation.",
                        "video": "",
                        "attachments": []
                    }
                ]
            }
        ],

        "Digital Marketing Masterclass": [
            {
                "section_title": "Marketing Intro",
                "lessons": [
                    {
                        "title": "What is Digital Marketing",
                        "content": "Overview of marketing.",
                        "video": "",
                        "attachments": []
                    }
                ]
            }
        ]
    }

    for course_name, sections in course_data.items():
        course = Course.objects.filter(title=course_name).first()

        if not course:
            print(f"❌ Course not found: {course_name}")
            continue

        print(f"✅ Processing: {course_name}")

        for sec_index, sec in enumerate(sections, start=1):

            # ✅ Prevent duplicate sections
            section, created = Section.objects.get_or_create(
                course=course,
                title=sec["section_title"],
                defaults={"order": sec_index}
            )

            if created:
                print(f"   ➕ Section created: {section.title}")
            else:
                print(f"   ⚠️ Section exists: {section.title}")

            for lesson_index, les in enumerate(sec["lessons"], start=1):

                # ✅ Prevent duplicate lessons
                lesson, created = Lesson.objects.get_or_create(
                    section=section,
                    title=les["title"],
                    defaults={
                        "content": les["content"],
                        "order": lesson_index,
                        "video": les["video"] if les["video"] else None
                    }
                )

                if created:
                    print(f"      ➕ Lesson created: {lesson.title}")
                else:
                    print(f"      ⚠️ Lesson exists: {lesson.title}")

                for att in les["attachments"]:
                    Attachment.objects.get_or_create(
                        lesson=lesson,
                        title=att["title"],
                        defaults={
                            "extra_url": att["url"],
                            "file_type": "other"
                        }
                    )

    print("🎉 DONE: Safe seeding complete!")