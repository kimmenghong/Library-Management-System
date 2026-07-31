import csv
import logging
import re
from io import StringIO

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate
from django.contrib.auth import login as django_login
from django.contrib.auth import logout as django_logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.files.base import ContentFile
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Q
from django.db.models.deletion import ProtectedError
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme

from .forms import (
    AuthorForm,
    BookForm,
    BorrowForm,
    CategoryForm,
    FineForm,
    FinePaymentForm,
    MemberForm,
    NotificationForm,
    PublisherForm,
    ReportForm,
    ReturnForm,
    RoleForm,
    SupabaseAuthLoginForm,
    SupabaseAuthRegisterForm,
    UserCreateForm,
    UserUpdateForm,
)
from .models import (
    Author,
    Book,
    BorrowRecord,
    Category,
    Fine,
    Member,
    Notification,
    Publisher,
    Report,
    Role,
    User,
)
from .services.supabase_auth import SupabaseAuthError, get_supabase_auth_service

LIST_PAGE_SIZE = 15
LOCAL_AUTH_BACKEND = "django.contrib.auth.backends.ModelBackend"

audit_logger = logging.getLogger("library.audit")
error_logger = logging.getLogger("library.errors")

PUBLIC_CATALOG_BOOKS = [
    {
        "title": "Harry Potter and the Sorcerer's Stone",
        "category": "Fantasy",
        "author": "J. K. Rowling",
        "isbn": "9780439708180",
        "year": 1997,
        "status": "Borrowed",
        "available_copies": 1,
        "cover": "images/books/harry_potter_1.jpg",
    },
    {
        "title": "Harry Potter and the Chamber of Secrets",
        "category": "Fantasy",
        "author": "J. K. Rowling",
        "isbn": "9780439064873",
        "year": 1998,
        "status": "Available",
        "available_copies": 3,
        "cover": "images/books/harry_potter_2.jpg",
    },
    {
        "title": "Harry Potter and the Prisoner of Azkaban",
        "category": "Fantasy",
        "author": "J. K. Rowling",
        "isbn": "9780439136365",
        "year": 1999,
        "status": "Reserved",
        "available_copies": 2,
        "cover": "images/books/harry_potter_3.jpg",
    },
    {
        "title": "Harry Potter and the Goblet of Fire",
        "category": "Fantasy",
        "author": "J. K. Rowling",
        "isbn": "9780439139601",
        "year": 2000,
        "status": "Available",
        "available_copies": 4,
        "cover": "images/books/harry_potter_4.jpg",
    },
    {
        "title": "Harry Potter and the Order of the Phoenix",
        "category": "Fantasy",
        "author": "J. K. Rowling",
        "isbn": "9780439358071",
        "year": 2003,
        "status": "Borrowed",
        "available_copies": 0,
        "cover": "images/books/harry_potter_5.jpg",
    },
    {
        "title": "Harry Potter and the Half-Blood Prince",
        "category": "Fantasy",
        "author": "J. K. Rowling",
        "isbn": "9780439785969",
        "year": 2005,
        "status": "Available",
        "available_copies": 3,
        "cover": "images/books/harry_potter_6.jpg",
    },
    {
        "title": "Harry Potter and the Deathly Hallows",
        "category": "Fantasy",
        "author": "J. K. Rowling",
        "isbn": "9780545010221",
        "year": 2007,
        "status": "Under Maintenance",
        "available_copies": 1,
        "cover": "images/books/harry_potter_7.jpg",
    },
    {
        "title": "The Hobbit",
        "category": "Adventure",
        "author": "J. R. R. Tolkien",
        "isbn": "9780547928227",
        "year": 1937,
        "status": "Available",
        "available_copies": 4,
        "cover": "images/books/the_hobbit.jpg",
    },
    {
        "title": "The Lord of the Rings",
        "category": "Fantasy",
        "author": "J. R. R. Tolkien",
        "isbn": "9780544003415",
        "year": 1954,
        "status": "Available",
        "available_copies": 3,
        "cover": "images/books/lord_of_the_rings.jpg",
    },
    {
        "title": "The Alchemist",
        "category": "Fiction",
        "author": "Paulo Coelho",
        "isbn": "9780061122415",
        "year": 1988,
        "status": "Borrowed",
        "available_copies": 0,
        "cover": "images/books/the_alchemist.jpg",
    },
    {
        "title": "Atomic Habits",
        "category": "Self-Help",
        "author": "James Clear",
        "isbn": "9780735211292",
        "year": 2018,
        "status": "Available",
        "available_copies": 5,
        "cover": "images/books/atomic_habits.jpg",
    },
    {
        "title": "Deep Work",
        "category": "Productivity",
        "author": "Cal Newport",
        "isbn": "9781455586691",
        "year": 2016,
        "status": "Reserved",
        "available_copies": 2,
        "cover": "images/books/deep_work.jpg",
    },
    {
        "title": "The Psychology of Money",
        "category": "Finance",
        "author": "Morgan Housel",
        "isbn": "9780857197689",
        "year": 2020,
        "status": "Available",
        "available_copies": 4,
        "cover": "images/books/psychology_of_money.jpg",
    },
    {
        "title": "Rich Dad Poor Dad",
        "category": "Finance",
        "author": "Robert Kiyosaki",
        "isbn": "9781612680194",
        "year": 1997,
        "status": "Available",
        "available_copies": 3,
        "cover": "images/books/rich_dad_poor_dad.jpg",
    },
    {
        "title": "Think and Grow Rich",
        "category": "Self-Help",
        "author": "Napoleon Hill",
        "isbn": "9781585424337",
        "year": 1937,
        "status": "Available",
        "available_copies": 3,
        "cover": "images/books/think_and_grow_rich.jpg",
    },
    {
        "title": "How to Win Friends and Influence People",
        "category": "Communication",
        "author": "Dale Carnegie",
        "isbn": "9780671027032",
        "year": 1936,
        "status": "Available",
        "available_copies": 4,
        "cover": "images/books/how_to_win_friends.jpg",
    },
    {
        "title": "The 7 Habits of Highly Effective People",
        "category": "Leadership",
        "author": "Stephen R. Covey",
        "isbn": "9781982137274",
        "year": 1989,
        "status": "Available",
        "available_copies": 3,
        "cover": "images/books/seven_habits.jpg",
    },
    {
        "title": "The Power of Habit",
        "category": "Psychology",
        "author": "Charles Duhigg",
        "isbn": "9780812981605",
        "year": 2012,
        "status": "Reserved",
        "available_copies": 1,
        "cover": "images/books/power_of_habit.jpg",
    },
    {
        "title": "Start With Why",
        "category": "Business",
        "author": "Simon Sinek",
        "isbn": "9781591846444",
        "year": 2009,
        "status": "Available",
        "available_copies": 5,
        "cover": "images/books/start_with_why.jpg",
    },
    {
        "title": "Zero to One",
        "category": "Entrepreneurship",
        "author": "Peter Thiel",
        "isbn": "9780804139298",
        "year": 2014,
        "status": "Available",
        "available_copies": 2,
        "cover": "images/books/zero_to_one.jpg",
    },
    {
        "title": "The Lean Startup",
        "category": "Business",
        "author": "Eric Ries",
        "isbn": "9780307887894",
        "year": 2011,
        "status": "Borrowed",
        "available_copies": 0,
        "cover": "images/books/lean_startup.jpg",
    },
    {
        "title": "Good to Great",
        "category": "Management",
        "author": "Jim Collins",
        "isbn": "9780066620992",
        "year": 2001,
        "status": "Available",
        "available_copies": 3,
        "cover": "images/books/good_to_great.jpg",
    },
    {
        "title": "Clean Code",
        "category": "Computer Science",
        "author": "Robert C. Martin",
        "isbn": "9780132350884",
        "year": 2008,
        "status": "Available",
        "available_copies": 4,
        "cover": "images/books/clean_code.jpg",
    },
    {
        "title": "Clean Architecture",
        "category": "Software Engineering",
        "author": "Robert C. Martin",
        "isbn": "9780134494166",
        "year": 2017,
        "status": "Under Maintenance",
        "available_copies": 1,
        "cover": "images/books/clean_architecture.jpg",
    },
    {
        "title": "Design Patterns",
        "category": "Software Engineering",
        "author": "Erich Gamma, Richard Helm, Ralph Johnson, John Vlissides",
        "isbn": "9780201633610",
        "year": 1994,
        "status": "Borrowed",
        "available_copies": 0,
        "cover": "images/books/design_patterns.jpg",
    },
    {
        "title": "Introduction to Algorithms",
        "category": "Algorithms",
        "author": "Thomas H. Cormen, Charles E. Leiserson, Ronald L. Rivest, Clifford Stein",
        "isbn": "9780262046305",
        "year": 2022,
        "status": "Available",
        "available_copies": 2,
        "cover": "images/books/introduction_to_algorithms.jpg",
    },
    {
        "title": "Artificial Intelligence: A Modern Approach",
        "category": "AI",
        "author": "Stuart Russell, Peter Norvig",
        "isbn": "9780134610993",
        "year": 2020,
        "status": "Available",
        "available_copies": 2,
        "cover": "images/books/ai_modern_approach.jpg",
    },
    {
        "title": "Python Crash Course",
        "category": "Programming",
        "author": "Eric Matthes",
        "isbn": "9781593279288",
        "year": 2015,
        "status": "Available",
        "available_copies": 5,
        "cover": "images/books/python_crash_course.jpg",
    },
    {
        "title": "Automate the Boring Stuff with Python",
        "category": "Programming",
        "author": "Al Sweigart",
        "isbn": "9781593279929",
        "year": 2019,
        "status": "Reserved",
        "available_copies": 2,
        "cover": "images/books/automate_boring_stuff.jpg",
    },
    {
        "title": "Head First Java",
        "category": "Programming",
        "author": "Kathy Sierra, Bert Bates",
        "isbn": "9780596009205",
        "year": 2003,
        "status": "Available",
        "available_copies": 4,
        "cover": "images/books/head_first_java.jpg",
    },
    {
        "title": "Effective Java",
        "category": "Programming",
        "author": "Joshua Bloch",
        "isbn": "9780134685991",
        "year": 2018,
        "status": "Borrowed",
        "available_copies": 0,
        "cover": "images/books/effective_java.jpg",
    },
    {
        "title": "Java: The Complete Reference",
        "category": "Programming",
        "author": "Herbert Schildt",
        "isbn": "9781260440232",
        "year": 2018,
        "status": "Available",
        "available_copies": 3,
        "cover": "images/books/java_complete_reference.jpg",
    },
    {
        "title": "Computer Networking",
        "category": "Networking",
        "author": "James Kurose, Keith Ross",
        "isbn": "9780133594140",
        "year": 2012,
        "status": "Available",
        "available_copies": 3,
        "cover": "images/books/computer_networking.jpg",
    },
    {
        "title": "Operating System Concepts",
        "category": "Operating Systems",
        "author": "Abraham Silberschatz, Peter B. Galvin, Greg Gagne",
        "isbn": "9781119456339",
        "year": 2018,
        "status": "Under Maintenance",
        "available_copies": 1,
        "cover": "images/books/operating_system_concepts.jpg",
    },
    {
        "title": "Database System Concepts",
        "category": "Database",
        "author": "Abraham Silberschatz, Henry F. Korth, S. Sudarshan",
        "isbn": "9780073523323",
        "year": 2010,
        "status": "Borrowed",
        "available_copies": 0,
        "cover": "images/books/database_system_concepts.jpg",
    },
    {
        "title": "Computer Organization and Design",
        "category": "Computer Architecture",
        "author": "David A. Patterson, John L. Hennessy",
        "isbn": "9780124077263",
        "year": 2013,
        "status": "Available",
        "available_copies": 3,
        "cover": "images/books/computer_organization_design.jpg",
    },
    {
        "title": "Software Engineering",
        "category": "Software Engineering",
        "author": "Ian Sommerville",
        "isbn": "9780137035151",
        "year": 2010,
        "status": "Reserved",
        "available_copies": 1,
        "cover": "images/books/software_engineering.jpg",
    },
    {
        "title": "The Pragmatic Programmer",
        "category": "Programming",
        "author": "Andrew Hunt, David Thomas",
        "isbn": "9780135957059",
        "year": 2019,
        "status": "Available",
        "available_copies": 4,
        "cover": "images/books/pragmatic_programmer.jpg",
    },
    {
        "title": "Code Complete",
        "category": "Programming",
        "author": "Steve McConnell",
        "isbn": "9780735619678",
        "year": 2004,
        "status": "Available",
        "available_copies": 2,
        "cover": "images/books/code_complete.jpg",
    },
    {
        "title": "Refactoring",
        "category": "Software Engineering",
        "author": "Martin Fowler",
        "isbn": "9780134757599",
        "year": 2018,
        "status": "Under Maintenance",
        "available_copies": 1,
        "cover": "images/books/refactoring.jpg",
    },
    {
        "title": "HTML and CSS",
        "category": "Web Development",
        "author": "Jon Duckett",
        "isbn": "9781118008188",
        "year": 2011,
        "status": "Available",
        "available_copies": 5,
        "cover": "images/books/html_css.jpg",
    },
    {
        "title": "JavaScript and JQuery",
        "category": "Web Development",
        "author": "Jon Duckett",
        "isbn": "9781118531648",
        "year": 2014,
        "status": "Available",
        "available_copies": 4,
        "cover": "images/books/javascript_jquery.jpg",
    },
    {
        "title": "Django for Beginners",
        "category": "Web Development",
        "author": "William S. Vincent",
        "isbn": "9781735467207",
        "year": 2022,
        "status": "Reserved",
        "available_copies": 2,
        "cover": "images/books/django_for_beginners.jpg",
    },
    {
        "title": "Diary of a Wimpy Kid",
        "category": "Comedy",
        "author": "Jeff Kinney",
        "isbn": "9781419741852",
        "year": 2007,
        "status": "Available",
        "available_copies": 6,
        "cover": "images/books/diary_wimpy_kid.jpg",
    },
    {
        "title": "To Kill a Mockingbird",
        "category": "Classic",
        "author": "Harper Lee",
        "isbn": "9780061120084",
        "year": 1960,
        "status": "Available",
        "available_copies": 4,
        "cover": "images/books/to_kill_mockingbird.jpg",
    },
    {
        "title": "Pride and Prejudice",
        "category": "Romance",
        "author": "Jane Austen",
        "isbn": "9780141439518",
        "year": 1813,
        "status": "Reserved",
        "available_copies": 2,
        "cover": "images/books/pride_prejudice.jpg",
    },
    {
        "title": "The Adventures of Sherlock Holmes",
        "category": "Mystery",
        "author": "Arthur Conan Doyle",
        "isbn": "9780140437713",
        "year": 1892,
        "status": "Available",
        "available_copies": 3,
        "cover": "images/books/adventures_sherlock_holmes.jpg",
    },
    {
        "title": "The Little Prince",
        "category": "Children",
        "author": "Antoine de Saint-Exupery",
        "isbn": "9780156012195",
        "year": 1943,
        "status": "Available",
        "available_copies": 5,
        "cover": "images/books/little_prince.jpg",
    },
    {
        "title": "1984",
        "category": "Dystopian",
        "author": "George Orwell",
        "isbn": "9780451524935",
        "year": 1949,
        "status": "Borrowed",
        "available_copies": 0,
        "cover": "images/books/nineteen_eighty_four.jpg",
    },
    {
        "title": "Animal Farm",
        "category": "Fiction",
        "author": "George Orwell",
        "isbn": "9780451526342",
        "year": 1945,
        "status": "Available",
        "available_copies": 4,
        "cover": "images/books/animal_farm.jpg",
    },
    {
        "title": "The Great Gatsby",
        "category": "Classic",
        "author": "F. Scott Fitzgerald",
        "isbn": "9780743273565",
        "year": 1925,
        "status": "Available",
        "available_copies": 3,
        "cover": "images/books/great_gatsby.jpg",
    },
    {
        "title": "The Old Man and the Sea",
        "category": "Fiction",
        "author": "Ernest Hemingway",
        "isbn": "9780684801223",
        "year": 1952,
        "status": "Under Maintenance",
        "available_copies": 1,
        "cover": "images/books/old_man_sea.jpg",
    },
    {
        "title": "The Kite Runner",
        "category": "Fiction",
        "author": "Khaled Hosseini",
        "isbn": "9781594480003",
        "year": 2003,
        "status": "Available",
        "available_copies": 3,
        "cover": "images/books/kite_runner.jpg",
    },
    {
        "title": "A Brief History of Time",
        "category": "Science",
        "author": "Stephen Hawking",
        "isbn": "9780553380163",
        "year": 1988,
        "status": "Available",
        "available_copies": 2,
        "cover": "images/books/brief_history_time.jpg",
    },
    {
        "title": "Sapiens",
        "category": "History",
        "author": "Yuval Noah Harari",
        "isbn": "9780062316097",
        "year": 2011,
        "status": "Borrowed",
        "available_copies": 0,
        "cover": "images/books/sapiens.jpg",
    },
    {
        "title": "The Art of War",
        "category": "Strategy",
        "author": "Sun Tzu",
        "isbn": "9781599869773",
        "year": 1910,
        "status": "Available",
        "available_copies": 4,
        "cover": "images/books/art_of_war.jpg",
    },
    {
        "title": "Educated",
        "category": "Biography",
        "author": "Tara Westover",
        "isbn": "9780399590504",
        "year": 2018,
        "status": "Reserved",
        "available_copies": 1,
        "cover": "images/books/educated.jpg",
    },
    {
        "title": "The Midnight Library",
        "category": "Fiction",
        "author": "Matt Haig",
        "isbn": "9780525559474",
        "code": "BK-2051",
        "year": 2020,
        "status": "Available",
        "available_copies": 12,
        "total_copies": 15,
        "edition": "First Edition",
        "publisher": "Canongate Books",
        "shelf_location": "FIC-A-01",
        "description": (
            "Between life and death there is a library filled with infinite "
            "possibilities. Nora Seed discovers she can experience different "
            "versions of her life and learn what truly makes life meaningful."
        ),
        "cover": "images/books/the_midnight_library.jpg",
    },
    {
        "title": "Ikigai: The Japanese Secret to a Long and Happy Life",
        "category": "Self-Help",
        "author": "Héctor García and Francesc Miralles",
        "isbn": "9780143130727",
        "code": "BK-2052",
        "year": 2017,
        "status": "Available",
        "available_copies": 8,
        "total_copies": 10,
        "edition": "First Edition",
        "publisher": "Penguin Books",
        "shelf_location": "SEL-B-02",
        "description": (
            "Discover the Japanese philosophy of finding purpose, happiness, "
            "and balance in everyday life through the concept of Ikigai."
        ),
        "cover": "images/books/ikigai.jpg",
    },
    {
        "title": "The Silent Patient",
        "category": "Mystery & Thriller",
        "author": "Alex Michaelides",
        "isbn": "9781250301697",
        "code": "BK-2053",
        "year": 2019,
        "status": "Borrowed",
        "available_copies": 5,
        "total_copies": 12,
        "edition": "First Edition",
        "publisher": "Celadon Books",
        "shelf_location": "MYS-C-03",
        "description": (
            "Alicia Berenson lives a seemingly perfect life until she shoots "
            "her husband and never speaks another word. A psychotherapist "
            "becomes obsessed with uncovering the truth behind her silence."
        ),
        "cover": "images/books/the_silent_patient.jpg",
    },
    {
        "title": "Becoming",
        "category": "Memoir",
        "author": "Michelle Obama",
        "isbn": "9781524763138",
        "year": 2018,
        "status": "Available",
        "available_copies": 3,
        "cover": "images/books/becoming.jpg",
    },
    {
        "title": "Charlie and the Chocolate Factory",
        "category": "Children's Literature",
        "author": "Roald Dahl",
        "isbn": "9780142410318",
        "year": 1964,
        "status": "Available",
        "available_copies": 3,
        "cover": "images/books/charlie_chocolate_factory.jpg",
    },
    {
        "title": "Charlotte's Web",
        "category": "Children's Literature",
        "author": "E. B. White",
        "isbn": "9780064400558",
        "year": 1952,
        "status": "Available",
        "available_copies": 3,
        "cover": "images/books/charlottes_web.jpg",
    },
    {
        "title": "Computer Networks",
        "category": "Computer Science",
        "author": "Andrew S. Tanenbaum",
        "isbn": "9780132126953",
        "year": 2010,
        "status": "Available",
        "available_copies": 2,
        "cover": "images/books/computer_networks.jpg",
    },
    {
        "title": "Dracula",
        "category": "Horror",
        "author": "Bram Stoker",
        "isbn": "9780486411095",
        "year": 1897,
        "status": "Available",
        "available_copies": 3,
        "cover": "images/books/dracula.jpg",
    },
    {
        "title": "Dune",
        "category": "Science Fiction",
        "author": "Frank Herbert",
        "isbn": "9780441172719",
        "year": 1965,
        "status": "Borrowed",
        "available_copies": 0,
        "cover": "images/books/dune.jpg",
    },
    {
        "title": "It",
        "category": "Horror",
        "author": "Stephen King",
        "isbn": "9781501142970",
        "year": 1986,
        "status": "Available",
        "available_copies": 3,
        "cover": "images/books/it_stephen_king.jpg",
    },
    {
        "title": "Macbeth",
        "category": "Drama",
        "author": "William Shakespeare",
        "isbn": "9780743477109",
        "year": 1606,
        "status": "Available",
        "available_copies": 3,
        "cover": "images/books/macbeth.jpg",
    },
    {
        "title": "Me Before You",
        "category": "Romance",
        "author": "Jojo Moyes",
        "isbn": "9780143124542",
        "year": 2012,
        "status": "Available",
        "available_copies": 3,
        "cover": "images/books/me_before_you.jpg",
    },
    {
        "title": "Romeo and Juliet",
        "category": "Drama",
        "author": "William Shakespeare",
        "isbn": "9780743477116",
        "year": 1597,
        "status": "Available",
        "available_copies": 3,
        "cover": "images/books/romeo_and_juliet.jpg",
    },
    {
        "title": "Sherlock Holmes: A Study in Scarlet",
        "category": "Mystery",
        "author": "Arthur Conan Doyle",
        "isbn": "9780140439083",
        "year": 1887,
        "status": "Available",
        "available_copies": 3,
        "cover": "images/books/study_in_scarlet.jpg",
    },
    {
        "title": "Steve Jobs",
        "category": "Biography",
        "author": "Walter Isaacson",
        "isbn": "9781451648539",
        "year": 2011,
        "status": "Available",
        "available_copies": 2,
        "cover": "images/books/steve_jobs.jpg",
    },
    {
        "title": "The Da Vinci Code",
        "category": "Mystery",
        "author": "Dan Brown",
        "isbn": "9780307474278",
        "year": 2003,
        "status": "Available",
        "available_copies": 3,
        "cover": "images/books/da_vinci_code.jpg",
    },
    {
        "title": "The Diary of a Young Girl",
        "category": "Biography",
        "author": "Anne Frank",
        "isbn": "9780553296983",
        "year": 1947,
        "status": "Borrowed",
        "available_copies": 0,
        "cover": "images/books/diary_young_girl.jpg",
    },
    {
        "title": "The Fault in Our Stars",
        "category": "Romance",
        "author": "John Green",
        "isbn": "9780525478812",
        "year": 2012,
        "status": "Available",
        "available_copies": 3,
        "cover": "images/books/fault_in_our_stars.jpg",
    },
    {
        "title": "The Hunger Games",
        "category": "Adventure",
        "author": "Suzanne Collins",
        "isbn": "9780439023528",
        "year": 2008,
        "status": "Available",
        "available_copies": 4,
        "cover": "images/books/hunger_games.jpg",
    },
    {
        "title": "The Maze Runner",
        "category": "Science Fiction",
        "author": "James Dashner",
        "isbn": "9780385737951",
        "year": 2009,
        "status": "Available",
        "available_copies": 3,
        "cover": "images/books/maze_runner.jpg",
    },
    {
        "title": "Wonder",
        "category": "Children's Literature",
        "author": "R. J. Palacio",
        "isbn": "9780375869020",
        "year": 2012,
        "status": "Available",
        "available_copies": 4,
        "cover": "images/books/wonder.jpg",
    },
]

PUBLIC_STATUS_CLASSES = {
    "Available": "text-bg-success",
    "Borrowed": "text-bg-warning",
    "Reserved": "text-bg-primary",
    "Under Maintenance": "text-bg-secondary",
    "Unavailable": "text-bg-danger",
}

PUBLIC_TECHNICAL_CATEGORIES = {
    "AI",
    "Algorithms",
    "Computer Architecture",
    "Computer Science",
    "Database",
    "Networking",
    "Operating Systems",
    "Programming",
    "Software Engineering",
    "Web Development",
}


def _public_book_description(book):
    return (
        f"{book['title']} by {book['author']} is a selected "
        f"{book['category'].lower()} title in the public university library "
        "catalog. Visitors can review its availability and bibliographic "
        "details before signing in or contacting the library desk."
    )


reserved_public_codes = {
    book["code"] for book in PUBLIC_CATALOG_BOOKS if book.get("code")
}
next_public_code_number = 2001

for index, book in enumerate(PUBLIC_CATALOG_BOOKS, start=1):
    available_copies = int(book["available_copies"])
    if not book.get("code"):
        while f"BK-{next_public_code_number}" in reserved_public_codes:
            next_public_code_number += 1
        book["code"] = f"BK-{next_public_code_number}"
        next_public_code_number += 1
    book["status_class"] = PUBLIC_STATUS_CLASSES.get(book["status"], "text-bg-light")
    book["publisher"] = book.get(
        "publisher",
        (
            "Pearson Education"
            if book["category"] in PUBLIC_TECHNICAL_CATEGORIES
            else "University Press"
        ),
    )
    book["edition"] = book.get("edition", "Demo Edition")
    book["shelf_location"] = book.get("shelf_location", f"PUB-{index:03d}")
    book["total_copies"] = book.get(
        "total_copies",
        max(available_copies + (0 if book["status"] == "Available" else 1), 1),
    )
    book["availability_label"] = (
        "Available now" if available_copies > 0 else "Currently unavailable"
    )
    book["availability_class"] = (
        "text-bg-success" if available_copies > 0 else "text-bg-danger"
    )
    book["description"] = book.get("description", _public_book_description(book))
    book["search_text"] = (
        f"{book['title']} {book['author']} {book['category']} "
        f"{book['isbn']} {book['code']} {book['status']} {book['year']} "
        f"{book['available_copies']} copies"
    ).lower()


PUBLIC_CATALOG_BY_ISBN = {book["isbn"]: book for book in PUBLIC_CATALOG_BOOKS}
PUBLIC_CATALOG_PAGE_SIZE = 12


def _public_catalog_querystring(request):
    query_params = request.GET.copy()
    allowed_keys = {"catalog_q", "catalog_status", "catalog_category", "catalog_page"}
    for key in list(query_params.keys()):
        if key not in allowed_keys:
            query_params.pop(key, None)
    return query_params.urlencode()


def _public_catalog_context(request):
    """Return filtered and paginated public catalog data for the login page."""

    query = request.GET.get("catalog_q", "").strip()
    selected_status = request.GET.get("catalog_status", "").strip()
    selected_category = request.GET.get("catalog_category", "").strip()
    catalog_books = list(PUBLIC_CATALOG_BOOKS)

    if query:
        term = query.lower()
        catalog_books = [book for book in catalog_books if term in book["search_text"]]

    if selected_status:
        catalog_books = [
            book for book in catalog_books if book["status"] == selected_status
        ]

    if selected_category:
        catalog_books = [
            book for book in catalog_books if book["category"] == selected_category
        ]

    paginator = Paginator(catalog_books, PUBLIC_CATALOG_PAGE_SIZE)
    page_obj = paginator.get_page(request.GET.get("catalog_page"))
    query_params = request.GET.copy()
    for key in list(query_params.keys()):
        if key not in {"catalog_q", "catalog_status", "catalog_category"}:
            query_params.pop(key, None)

    return {
        "public_catalog_books": page_obj.object_list,
        "public_catalog_page": page_obj,
        "public_catalog_query": query,
        "public_catalog_selected_status": selected_status,
        "public_catalog_selected_category": selected_category,
        "public_catalog_statuses": list(PUBLIC_STATUS_CLASSES.keys()),
        "public_catalog_categories": sorted(
            {book["category"] for book in PUBLIC_CATALOG_BOOKS}
        ),
        "public_catalog_total": len(PUBLIC_CATALOG_BOOKS),
        "public_catalog_filtered_count": len(catalog_books),
        "public_catalog_querystring": query_params.urlencode(),
    }


def _get_public_catalog_book(book_code):
    normalized_code = book_code.strip().upper()
    for book in PUBLIC_CATALOG_BOOKS:
        if book["code"] == normalized_code:
            return book
    raise Http404("Public catalog book not found.")


def _public_book_related(book):
    related = [
        item
        for item in PUBLIC_CATALOG_BOOKS
        if item["category"] == book["category"] and item["code"] != book["code"]
    ]
    return related[:4]


def _public_catalog_back_url(request):
    querystring = _public_catalog_querystring(request)
    base_url = reverse("library:login")
    if querystring:
        return f"{base_url}?{querystring}#public-search"
    return f"{base_url}#public-search"


def _attach_public_catalog_metadata(book_page):
    for book in book_page.object_list:
        public_book = PUBLIC_CATALOG_BY_ISBN.get(book.isbn)
        book.public_catalog_cover = public_book["cover"] if public_book else ""
        book.public_catalog_code = public_book["code"] if public_book else ""


class LocalUserSyncError(Exception):
    """Raised when a Supabase identity cannot be mapped to a local user."""


def is_library_staff(user):
    """Return True when a user may access staff library workflows."""

    if not user.is_authenticated:
        return False
    return user.can_manage_library


staff_required = user_passes_test(is_library_staff, login_url="library:login")


def _require_capability(allowed):
    if not allowed:
        raise PermissionDenied("You do not have permission to access this page.")


def _can_manage_entity(user, entity):
    if entity in {"roles", "users"}:
        return user.can_manage_users
    if entity in {"categories", "authors", "publishers"}:
        return user.can_manage_catalog
    if entity == "members":
        return user.can_manage_circulation
    return False


ENTITY_CONFIG = {
    "roles": {
        "model": Role,
        "form": RoleForm,
        "title": "Roles",
        "headers": ["ID", "Role name", "Description"],
        "row": lambda item: [item.role_id, item.role_name, item.description or "-"],
    },
    "users": {
        "model": User,
        "create_form": UserCreateForm,
        "update_form": UserUpdateForm,
        "title": "Users",
        "headers": ["ID", "Username", "Full name", "Role", "Active"],
        "row": lambda item: [
            item.user_id,
            item.username,
            item.full_name,
            item.role.role_name,
            "Yes" if item.is_active else "No",
        ],
        "queryset": lambda: User.objects.select_related("role"),
    },
    "categories": {
        "model": Category,
        "form": CategoryForm,
        "title": "Categories",
        "headers": ["ID", "Category name", "Description"],
        "row": lambda item: [
            item.category_id,
            item.category_name,
            item.description or "-",
        ],
    },
    "authors": {
        "model": Author,
        "form": AuthorForm,
        "title": "Authors",
        "headers": ["ID", "Author name", "Biography"],
        "row": lambda item: [
            item.author_id,
            item.author_name,
            item.biography or "-",
        ],
    },
    "publishers": {
        "model": Publisher,
        "form": PublisherForm,
        "title": "Publishers",
        "headers": ["ID", "Publisher name", "Contact", "Email"],
        "row": lambda item: [
            item.publisher_id,
            item.publisher_name,
            item.contact_number or "-",
            item.email or "-",
        ],
    },
    "members": {
        "model": Member,
        "form": MemberForm,
        "title": "Members",
        "headers": ["ID", "Code", "Name", "Type", "Department", "Status"],
        "row": lambda item: [
            item.member_id,
            item.member_code,
            item.user.full_name,
            item.get_member_type_display(),
            item.department or "-",
            item.get_status_display(),
        ],
        "queryset": lambda: Member.objects.select_related("user"),
    },
}


def _entity_config(entity):
    try:
        return ENTITY_CONFIG[entity]
    except KeyError as exc:
        raise Http404("Unknown library data type.") from exc


def _entity_queryset(config):
    factory = config.get("queryset")
    return factory() if factory else config["model"].objects.all()


def _paginate(request, queryset, per_page=LIST_PAGE_SIZE):
    """Return a page object while tolerating invalid page numbers."""

    return Paginator(queryset, per_page).get_page(request.GET.get("page"))


def _pagination_context(request, page_obj):
    params = request.GET.copy()
    params.pop("page", None)
    return {"page_obj": page_obj, "pagination_query": params.urlencode()}


def _overdue_records_filter():
    """Return a read-only query filter for active overdue borrow records."""
    today = timezone.localdate()
    return Q(status=BorrowRecord.OVERDUE) | Q(
        status=BorrowRecord.BORROWED,
        due_date__lt=today,
        return_date__isnull=True,
    )


def _safe_next_url(request):
    next_url = request.POST.get("next") or request.GET.get("next")
    if next_url and url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return next_url
    return settings.LOGIN_REDIRECT_URL


def _mark_book_issued(book):
    book.available_quantity -= 1
    book.status = Book.BORROWED if book.available_quantity == 0 else Book.AVAILABLE
    book.save(update_fields=["available_quantity", "status", "updated_at"])


def _mark_book_returned(book):
    previous_status = book.status
    book.available_quantity = min(book.quantity, book.available_quantity + 1)
    if previous_status == Book.BORROWED and book.available_quantity > 0:
        book.status = Book.AVAILABLE
    book.save(update_fields=["available_quantity", "status", "updated_at"])


def _store_supabase_session(request, identity):
    """Store non-sensitive Supabase identity metadata in the Django session."""

    request.session[settings.SUPABASE_AUTH_SESSION_KEY] = {
        "user_id": identity.supabase_user_id,
        "email": identity.email,
        "has_session": identity.has_session,
    }


def _clear_supabase_session(request):
    request.session.pop(settings.SUPABASE_AUTH_SESSION_KEY, None)


def _validate_local_login_user(user):
    if not user.is_active:
        raise LocalUserSyncError("This local library account is inactive.")
    if not user.role_id:
        raise LocalUserSyncError(
            "This local library account has no role assigned. "
            "Please contact the library administrator."
        )
    return user


def _default_supabase_role():
    role = Role.objects.filter(
        role_name__iexact=settings.SUPABASE_AUTH_DEFAULT_ROLE
    ).first()
    if not role:
        raise LocalUserSyncError(
            f"Default role '{settings.SUPABASE_AUTH_DEFAULT_ROLE}' does not exist."
        )
    return role


def _username_from_email(email):
    base = re.sub(r"[^a-zA-Z0-9_.-]+", "_", email.split("@", 1)[0]).strip("._-")
    base = (base or "user")[:40]
    username = base
    counter = 1
    while User.objects.filter(username=username).exists():
        suffix = f"_{counter}"
        username = f"{base[: 50 - len(suffix)]}{suffix}"
        counter += 1
    return username


@transaction.atomic
def _sync_supabase_identity(identity, *, create_if_missing=False, profile=None):
    profile = profile or {}
    email = identity.email.strip().lower()
    user = User.objects.select_related("role").filter(email__iexact=email).first()

    if not user:
        if not create_if_missing and settings.SUPABASE_AUTH_REQUIRE_LOCAL_USER:
            raise LocalUserSyncError(
                "No local library account exists for this Supabase user."
            )
        role = _default_supabase_role()
        user = User(
            role=role,
            username=_username_from_email(email),
            email=email,
            full_name=profile.get("full_name") or email.split("@", 1)[0],
            phone=profile.get("phone", ""),
            address=profile.get("address", ""),
            is_active=True,
            is_staff=False,
            is_superuser=False,
        )
        user.set_unusable_password()
        user.full_clean()
        user.save()
    else:
        changed_fields = []
        normalized_email = User.objects.normalize_email(email)
        if user.email != normalized_email:
            user.email = normalized_email
            changed_fields.append("email")
        for field in ("full_name", "phone", "address"):
            value = profile.get(field)
            if value and getattr(user, field) != value:
                setattr(user, field, value)
                changed_fields.append(field)
        if changed_fields:
            try:
                user.full_clean()
                user.save(update_fields=changed_fields + ["updated_at"])
            except ValidationError as exc:
                raise LocalUserSyncError("; ".join(exc.messages)) from exc

    return _validate_local_login_user(user)


def _local_fallback_authenticate(request, *, identifier, password):
    user = User.objects.select_related("role").filter(email__iexact=identifier).first()
    if not user:
        user = User.objects.select_related("role").filter(username=identifier).first()
    if not user:
        return None
    _validate_local_login_user(user)
    authenticated = authenticate(
        request,
        username=user.username,
        password=password,
    )
    if authenticated:
        return _validate_local_login_user(
            User.objects.select_related("role").get(pk=authenticated.pk)
        )
    return None


def _login_local_user(request, user):
    user.backend = LOCAL_AUTH_BACKEND
    django_login(request, user)


def register_view(request):
    if request.user.is_authenticated:
        return redirect(settings.LOGIN_REDIRECT_URL)

    form = SupabaseAuthRegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        if not settings.USE_SUPABASE_AUTH:
            form.add_error(
                None,
                "Supabase Auth is not enabled yet. Please configure Supabase first.",
            )
        else:
            try:
                identity = get_supabase_auth_service().sign_up(
                    email=form.cleaned_data["email"],
                    password=form.cleaned_data["password"],
                    metadata={
                        "full_name": form.cleaned_data["full_name"],
                        "phone": form.cleaned_data.get("phone", ""),
                    },
                )
                user = _sync_supabase_identity(
                    identity,
                    create_if_missing=True,
                    profile={
                        "full_name": form.cleaned_data["full_name"],
                        "phone": form.cleaned_data.get("phone", ""),
                        "address": form.cleaned_data.get("address", ""),
                    },
                )
                if identity.has_session:
                    _store_supabase_session(request, identity)
                    _login_local_user(request, user)
                    messages.success(request, "Registration completed successfully.")
                    return redirect(settings.LOGIN_REDIRECT_URL)

                messages.success(
                    request,
                    "Registration created. Please confirm your email before login.",
                )
                return redirect("library:login")
            except (SupabaseAuthError, LocalUserSyncError) as exc:
                form.add_error(None, getattr(exc, "message", str(exc)))

    return render(
        request,
        "library/register.html",
        {"form": form, "use_supabase_auth": settings.USE_SUPABASE_AUTH},
    )


def login_view(request):
    if request.user.is_authenticated:
        return redirect(_safe_next_url(request))

    form = SupabaseAuthLoginForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        identifier = form.cleaned_data["email"]
        password = form.cleaned_data["password"]
        try:
            if settings.USE_SUPABASE_AUTH:
                identity = get_supabase_auth_service().sign_in_with_password(
                    email=identifier,
                    password=password,
                )
                user = _sync_supabase_identity(identity)
                _store_supabase_session(request, identity)
            else:
                user = _local_fallback_authenticate(
                    request,
                    identifier=identifier,
                    password=password,
                )
                if not user:
                    raise LocalUserSyncError("Invalid email/username or password.")

            _login_local_user(request, user)
            audit_logger.info(
                "auth.library_login user_id=%s username=%s supabase=%s",
                user.pk,
                user.username,
                settings.USE_SUPABASE_AUTH,
            )
            return redirect(_safe_next_url(request))
        except (SupabaseAuthError, LocalUserSyncError) as exc:
            audit_logger.warning(
                "auth.library_login_failed identifier=%s supabase=%s",
                identifier,
                settings.USE_SUPABASE_AUTH,
            )
            form.add_error(None, getattr(exc, "message", str(exc)))

    return render(
        request,
        "library/login.html",
        {
            "form": form,
            "next": request.POST.get("next") or request.GET.get("next", ""),
            "use_supabase_auth": settings.USE_SUPABASE_AUTH,
            **_public_catalog_context(request),
        },
    )


def public_book_detail(request, book_code):
    book = _get_public_catalog_book(book_code)
    return render(
        request,
        "library/public_book_detail.html",
        {
            "book": book,
            "related_books": _public_book_related(book),
            "back_to_catalog_url": _public_catalog_back_url(request),
            "catalog_state_querystring": _public_catalog_querystring(request),
            "reservation_supported": False,
        },
    )


@login_required
def logout_view(request):
    if request.method == "POST":
        _clear_supabase_session(request)
        django_logout(request)
        messages.success(request, "You have been logged out.")
        return redirect(settings.LOGOUT_REDIRECT_URL)
    return redirect(settings.LOGIN_REDIRECT_URL)


@login_required
def dashboard(request):
    recent_borrows = BorrowRecord.objects.select_related(
        "member__user", "book", "issued_by", "received_by"
    )
    if not is_library_staff(request.user):
        recent_borrows = recent_borrows.filter(member__user=request.user)

    context = {
        "total_books": Book.objects.count(),
        "total_members": Member.objects.count(),
        "available_books": Book.objects.filter(available_quantity__gt=0).count(),
        "borrowed_books": BorrowRecord.objects.filter(
            status__in=[BorrowRecord.BORROWED, BorrowRecord.OVERDUE]
        ).count(),
        "overdue_books": BorrowRecord.objects.filter(_overdue_records_filter()).count(),
        "unpaid_fines": Fine.objects.exclude(
            status__in=[Fine.PAID, Fine.WAIVED]
        ).count(),
        "recent_borrows": recent_borrows[:8],
        "can_manage": is_library_staff(request.user),
    }
    return render(request, "library/dashboard.html", context)


@staff_required
def entity_list(request, entity):
    config = _entity_config(entity)
    _require_capability(_can_manage_entity(request.user, entity))
    page_obj = _paginate(request, _entity_queryset(config))
    objects = page_obj.object_list
    rows = [{"pk": item.pk, "values": config["row"](item)} for item in objects]
    return render(
        request,
        "library/entity_list.html",
        {
            "entity": entity,
            "title": config["title"],
            "headers": config["headers"],
            "rows": rows,
            **_pagination_context(request, page_obj),
        },
    )


@staff_required
def entity_create(request, entity):
    config = _entity_config(entity)
    _require_capability(_can_manage_entity(request.user, entity))
    form_class = config.get("create_form", config.get("form"))
    form = form_class(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, f"{config['title'][:-1]} created successfully.")
        return redirect("library:entity_list", entity=entity)
    return render(
        request,
        "library/entity_form.html",
        {"form": form, "title": f"Add {config['title'][:-1]}", "entity": entity},
    )


@staff_required
def entity_update(request, entity, pk):
    config = _entity_config(entity)
    _require_capability(_can_manage_entity(request.user, entity))
    instance = get_object_or_404(config["model"], pk=pk)
    form_class = config.get("update_form", config.get("form"))
    form = form_class(request.POST or None, instance=instance)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, f"{config['title'][:-1]} updated successfully.")
        return redirect("library:entity_list", entity=entity)
    return render(
        request,
        "library/entity_form.html",
        {
            "form": form,
            "title": f"Edit {config['title'][:-1]}",
            "entity": entity,
        },
    )


@staff_required
def entity_delete(request, entity, pk):
    config = _entity_config(entity)
    _require_capability(_can_manage_entity(request.user, entity))
    instance = get_object_or_404(config["model"], pk=pk)
    if request.method == "POST":
        try:
            instance.delete()
            messages.success(request, f"{config['title'][:-1]} deleted successfully.")
        except ProtectedError:
            error_logger.warning(
                "delete.protected entity=%s pk=%s user_id=%s",
                entity,
                pk,
                request.user.pk,
            )
            messages.error(
                request,
                (
                    "This record is referenced by other library data and "
                    "cannot be deleted."
                ),
            )
        return redirect("library:entity_list", entity=entity)
    return render(
        request,
        "library/confirm_delete.html",
        {"object": instance, "title": f"Delete {config['title'][:-1]}"},
    )


@login_required
def book_list(request):
    books = Book.objects.select_related("author", "publisher", "category")
    query = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()
    category = request.GET.get("category", "").strip()

    if query:
        books = books.filter(
            Q(title__icontains=query)
            | Q(isbn__icontains=query)
            | Q(author__author_name__icontains=query)
            | Q(publisher__publisher_name__icontains=query)
            | Q(category__category_name__icontains=query)
            | Q(shelf_location__icontains=query)
        )
    if status:
        books = books.filter(status=status)
    if category and category.isdigit():
        books = books.filter(category_id=category)
    page_obj = _paginate(request, books)
    _attach_public_catalog_metadata(page_obj)

    return render(
        request,
        "library/book_list.html",
        {
            "books": page_obj,
            "categories": Category.objects.all(),
            "status_choices": Book.STATUS_CHOICES,
            "query": query,
            "selected_status": status,
            "selected_category": category,
            "can_manage": is_library_staff(request.user),
            **_pagination_context(request, page_obj),
        },
    )


@staff_required
def book_create(request):
    _require_capability(request.user.can_manage_catalog)
    form = BookForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Book created successfully.")
        return redirect("library:book_list")
    return render(
        request,
        "library/entity_form.html",
        {"form": form, "title": "Add Book", "cancel_url": "library:book_list"},
    )


@staff_required
def book_update(request, pk):
    _require_capability(request.user.can_manage_catalog)
    book = get_object_or_404(Book, pk=pk)
    form = BookForm(request.POST or None, instance=book)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Book updated successfully.")
        return redirect("library:book_list")
    return render(
        request,
        "library/entity_form.html",
        {"form": form, "title": "Edit Book", "cancel_url": "library:book_list"},
    )


@staff_required
def book_delete(request, pk):
    _require_capability(request.user.can_manage_catalog)
    book = get_object_or_404(Book, pk=pk)
    if request.method == "POST":
        try:
            book.delete()
            messages.success(request, "Book deleted successfully.")
        except ProtectedError:
            error_logger.warning(
                "book.delete_protected book_id=%s user_id=%s", pk, request.user.pk
            )
            messages.error(request, "A book with borrowing history cannot be deleted.")
        return redirect("library:book_list")
    return render(
        request,
        "library/confirm_delete.html",
        {"object": book, "title": "Delete Book", "cancel_url": "library:book_list"},
    )


@login_required
def borrow_list(request):
    records = BorrowRecord.objects.select_related(
        "member__user", "book", "issued_by", "received_by"
    )
    if not is_library_staff(request.user):
        records = records.filter(member__user=request.user)
    status = request.GET.get("status", "").strip()
    if status == BorrowRecord.OVERDUE:
        records = records.filter(_overdue_records_filter())
    elif status == BorrowRecord.BORROWED:
        records = records.filter(
            status=BorrowRecord.BORROWED,
            due_date__gte=timezone.localdate(),
            return_date__isnull=True,
        )
    elif status:
        records = records.filter(status=status)
    page_obj = _paginate(request, records)
    return render(
        request,
        "library/borrow_list.html",
        {
            "records": page_obj,
            "status_choices": BorrowRecord.STATUS_CHOICES,
            "selected_status": status,
            "can_manage": is_library_staff(request.user),
            **_pagination_context(request, page_obj),
        },
    )


@staff_required
@transaction.atomic
def borrow_create(request):
    _require_capability(request.user.can_manage_circulation)
    form = BorrowForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        book = Book.objects.select_for_update().get(pk=form.cleaned_data["book"].pk)
        if book.available_quantity < 1 or book.status != Book.AVAILABLE:
            form.add_error("book", "This book is no longer available.")
        else:
            borrow_record = form.save(commit=False)
            borrow_record.book = book
            borrow_record.issued_by = request.user
            borrow_record.status = BorrowRecord.BORROWED
            borrow_record.save()

            _mark_book_issued(book)
            audit_logger.info(
                "borrow.issue borrow_id=%s member_id=%s book_id=%s issued_by=%s",
                borrow_record.pk,
                borrow_record.member_id,
                borrow_record.book_id,
                request.user.pk,
            )

            messages.success(request, "Book issued successfully.")
            return redirect("library:borrow_list")
    return render(request, "library/borrow_form.html", {"form": form})


@staff_required
@transaction.atomic
def borrow_return(request, pk):
    _require_capability(request.user.can_manage_circulation)
    borrow_record = get_object_or_404(
        BorrowRecord.objects.select_for_update().select_related("book", "member__user"),
        pk=pk,
    )
    if borrow_record.status not in {BorrowRecord.BORROWED, BorrowRecord.OVERDUE}:
        messages.error(request, "Only active borrow records can be returned.")
        return redirect("library:borrow_list")

    form = ReturnForm(request.POST or None, borrow_record=borrow_record)
    if request.method == "POST" and form.is_valid():
        return_date = form.cleaned_data["return_date"]
        borrow_record.return_date = return_date
        borrow_record.received_by = request.user
        borrow_record.status = BorrowRecord.RETURNED
        borrow_record.save()

        book = Book.objects.select_for_update().get(pk=borrow_record.book_id)
        _mark_book_returned(book)

        days_overdue = max((return_date - borrow_record.due_date).days, 0)
        if days_overdue:
            amount = settings.FINE_RATE_PER_DAY * days_overdue
            fine = Fine.objects.filter(
                borrow=borrow_record, member=borrow_record.member
            ).first()
            if fine:
                fine.amount = amount
                if fine.paid_amount > amount:
                    fine.paid_amount = amount
                fine.status = Fine.PAID if fine.paid_amount == amount else Fine.UNPAID
                fine.paid_date = timezone.now() if fine.status == Fine.PAID else None
                fine.save()
            else:
                Fine.objects.create(
                    borrow=borrow_record,
                    member=borrow_record.member,
                    amount=amount,
                )
            Notification.objects.create(
                member=borrow_record.member,
                title="Overdue fine created",
                message=(
                    f"A fine of {amount} was created for returning "
                    f"{borrow_record.book.title} {days_overdue} day(s) late."
                ),
                notification_type=Notification.FINE,
            )

        audit_logger.info(
            (
                "borrow.return borrow_id=%s member_id=%s book_id=%s "
                "received_by=%s days_overdue=%s"
            ),
            borrow_record.pk,
            borrow_record.member_id,
            borrow_record.book_id,
            request.user.pk,
            days_overdue,
        )

        messages.success(request, "Book returned successfully.")
        return redirect("library:borrow_list")
    return render(
        request,
        "library/return_form.html",
        {"form": form, "borrow_record": borrow_record},
    )


@login_required
def fine_list(request):
    fines = Fine.objects.select_related("borrow__book", "member__user")
    if not is_library_staff(request.user):
        fines = fines.filter(member__user=request.user)
    page_obj = _paginate(request, fines)
    return render(
        request,
        "library/fine_list.html",
        {
            "fines": page_obj,
            "can_manage": is_library_staff(request.user),
            **_pagination_context(request, page_obj),
        },
    )


@staff_required
def fine_create(request):
    _require_capability(request.user.can_manage_circulation)
    form = FineForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Fine saved successfully.")
        return redirect("library:fine_list")
    return render(
        request,
        "library/entity_form.html",
        {"form": form, "title": "Add Fine", "cancel_url": "library:fine_list"},
    )


@staff_required
@transaction.atomic
def fine_pay(request, pk):
    _require_capability(request.user.can_manage_circulation)
    fine = get_object_or_404(
        Fine.objects.select_for_update().select_related("member__user", "borrow__book"),
        pk=pk,
    )
    if fine.status in {Fine.PAID, Fine.WAIVED}:
        messages.info(request, "This fine has no payable balance.")
        return redirect("library:fine_list")

    form = FinePaymentForm(request.POST or None, fine=fine)
    if request.method == "POST" and form.is_valid():
        fine.paid_amount += form.cleaned_data["payment_amount"]
        if fine.paid_amount == fine.amount:
            fine.status = Fine.PAID
            fine.paid_date = timezone.now()
        else:
            fine.status = Fine.PARTIALLY_PAID
            fine.paid_date = None
        fine.save()
        audit_logger.info(
            "fine.payment fine_id=%s member_id=%s amount=%s user_id=%s",
            fine.pk,
            fine.member_id,
            form.cleaned_data["payment_amount"],
            request.user.pk,
        )
        messages.success(request, "Fine payment recorded successfully.")
        return redirect("library:fine_list")
    return render(
        request,
        "library/fine_payment_form.html",
        {"form": form, "fine": fine},
    )


@login_required
def notification_list(request):
    notifications = Notification.objects.select_related("member__user")
    if not is_library_staff(request.user):
        notifications = notifications.filter(member__user=request.user)
    page_obj = _paginate(request, notifications)
    return render(
        request,
        "library/notification_list.html",
        {
            "notifications": page_obj,
            "can_manage": is_library_staff(request.user),
            **_pagination_context(request, page_obj),
        },
    )


@staff_required
def notification_create(request):
    _require_capability(request.user.can_manage_circulation)
    form = NotificationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Member notification created successfully.")
        return redirect("library:notification_list")
    return render(
        request,
        "library/entity_form.html",
        {
            "form": form,
            "title": "Add Notification",
            "cancel_url": "library:notification_list",
        },
    )


@login_required
def notification_read(request, pk):
    notification = get_object_or_404(
        Notification.objects.select_related("member__user"), pk=pk
    )
    if not is_library_staff(request.user):
        get_object_or_404(Member, pk=notification.member_id, user=request.user)
    if request.method == "POST":
        notification.is_read = True
        notification.save(update_fields=["is_read"])
    return redirect("library:notification_list")


def _report_rows(report_type):
    if report_type == Report.BOOKS:
        yield ["Book ID", "Title", "ISBN", "Author", "Available", "Status"]
        for book in Book.objects.select_related("author"):
            yield [
                book.book_id,
                book.title,
                book.isbn,
                book.author.author_name,
                book.available_quantity,
                book.status,
            ]
    elif report_type == Report.MEMBERS:
        yield ["Member ID", "Code", "Name", "Type", "Department", "Status"]
        for member in Member.objects.select_related("user"):
            yield [
                member.member_id,
                member.member_code,
                member.user.full_name,
                member.member_type,
                member.department,
                member.status,
            ]
    elif report_type == Report.BORROWING:
        yield ["Borrow ID", "Member", "Book", "Borrowed", "Due", "Returned", "Status"]
        for record in BorrowRecord.objects.select_related("member", "book"):
            yield [
                record.borrow_id,
                record.member.member_code,
                record.book.title,
                record.borrow_date,
                record.due_date,
                record.return_date or "",
                record.effective_status,
            ]
    else:
        yield ["Fine ID", "Member", "Book", "Amount", "Paid", "Balance", "Status"]
        for fine in Fine.objects.select_related("member", "borrow__book"):
            yield [
                fine.fine_id,
                fine.member.member_code,
                fine.borrow.book.title,
                fine.amount,
                fine.paid_amount,
                fine.balance,
                fine.status,
            ]


def _create_report_file(report):
    output = StringIO()
    writer = csv.writer(output)
    writer.writerows(_report_rows(report.report_type))
    filename = (
        f"{report.report_type}_report_"
        f"{timezone.localtime(report.generated_at):%Y%m%d_%H%M%S}.csv"
    )
    report.file_path.save(
        filename,
        ContentFile(output.getvalue().encode("utf-8")),
        save=True,
    )


@staff_required
def report_list(request):
    _require_capability(request.user.can_manage_reports)
    reports = Report.objects.select_related("generated_by")
    borrowing_summary = (
        Book.objects.annotate(borrow_count=Count("borrow_records"))
        .filter(borrow_count__gt=0)
        .order_by("-borrow_count", "title")[:5]
    )
    page_obj = _paginate(request, reports)
    return render(
        request,
        "library/report_list.html",
        {
            "reports": page_obj,
            "borrowing_summary": borrowing_summary,
            **_pagination_context(request, page_obj),
        },
    )


@staff_required
def report_create(request):
    _require_capability(request.user.can_manage_reports)
    form = ReportForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        report = form.save(commit=False)
        report.generated_by = request.user
        report.save()
        if not report.file_path:
            _create_report_file(report)
        audit_logger.info(
            "report.generate report_id=%s report_type=%s generated_by=%s",
            report.pk,
            report.report_type,
            request.user.pk,
        )
        messages.success(request, "Report generated successfully.")
        return redirect("library:report_list")
    return render(
        request,
        "library/entity_form.html",
        {"form": form, "title": "Generate Report", "cancel_url": "library:report_list"},
    )
