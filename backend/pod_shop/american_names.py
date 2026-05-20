# List of 500 common American names
AMERICAN_NAMES = [
    # Male names
    "James Anderson", "Michael Johnson", "Robert Williams", "John Brown", "David Jones",
    "William Garcia", "Richard Martinez", "Joseph Rodriguez", "Thomas Hernandez", "Christopher Lopez",
    "Charles Wilson", "Daniel Moore", "Matthew Taylor", "Anthony Thomas", "Mark Jackson",
    "Donald White", "Steven Harris", "Andrew Martin", "Paul Thompson", "Joshua Garcia",
    "Kenneth Martinez", "Kevin Robinson", "Brian Clark", "George Rodriguez", "Timothy Lewis",
    "Ronald Lee", "Edward Walker", "Jason Hall", "Jeffrey Allen", "Ryan Young",
    "Jacob Hernandez", "Gary King", "Nicholas Wright", "Eric Lopez", "Jonathan Hill",
    "Stephen Scott", "Larry Green", "Justin Adams", "Scott Baker", "Brandon Nelson",
    "Raymond Carter", "Frank Mitchell", "Benjamin Perez", "Gregory Roberts", "Samuel Turner",
    "Patrick Phillips", "Alexander Campbell", "Jack Parker", "Dennis Evans", "Jerry Edwards",
    
    # Female names
    "Mary Smith", "Patricia Johnson", "Jennifer Williams", "Linda Brown", "Barbara Jones",
    "Elizabeth Garcia", "Susan Martinez", "Jessica Rodriguez", "Sarah Hernandez", "Karen Lopez",
    "Nancy Wilson", "Lisa Moore", "Betty Taylor", "Margaret Thomas", "Sandra Jackson",
    "Ashley White", "Kimberly Harris", "Emily Martin", "Donna Thompson", "Michelle Garcia",
    "Carol Martinez", "Amanda Robinson", "Melissa Clark", "Deborah Rodriguez", "Stephanie Lewis",
    "Dorothy Lee", "Rebecca Walker", "Sharon Hall", "Laura Allen", "Cynthia Young",
    "Amy Hernandez", "Kathleen King", "Angela Wright", "Shirley Lopez", "Brenda Hill",
    "Emma Scott", "Anna Green", "Pamela Adams", "Nicole Baker", "Samantha Nelson",
    "Katherine Carter", "Christine Mitchell", "Debra Perez", "Rachel Roberts", "Carolyn Turner",
    "Janet Phillips", "Maria Campbell", "Catherine Parker", "Heather Evans", "Diane Edwards",
    
    # More male names
    "Carl Collins", "Roger Stewart", "Keith Morris", "Gerald Rogers", "Walter Reed",
    "Randy Cook", "Albert Morgan", "Eugene Bell", "Vincent Murphy", "Russell Bailey",
    "Louis Rivera", "Philip Cooper", "Wayne Richardson", "Bobby Cox", "Douglas Howard",
    "Willie Ward", "Aaron Torres", "Jose Peterson", "Henry Gray", "Ralph Ramirez",
    "Johnny James", "Lawrence Watson", "Joe Brooks", "Bruce Kelly", "Arthur Sanders",
    "Roy Price", "Noah Bennett", "Harold Wood", "Billy Barnes", "Jordan Ross",
    "Dylan Henderson", "Logan Coleman", "Mason Jenkins", "Lucas Perry", "Ethan Powell",
    "Oliver Long", "Aiden Patterson", "Elijah Hughes", "James Flores", "Michael Washington",
    "Alexander Butler", "Daniel Simmons", "Matthew Foster", "Jackson Gonzales", "David Bryant",
    "Joseph Alexander", "Samuel Russell", "Henry Griffin", "Owen Diaz", "Sebastian Hayes",
    
    # More female names
    "Ruth Myers", "Virginia Ford", "Frances Hamilton", "Ann Graham", "Joyce Sullivan",
    "Diane Wallace", "Alice Woods", "Julie Cole", "Evelyn West", "Gloria Jordan",
    "Cheryl Owens", "Teresa Reynolds", "Doris Fisher", "Gloria Ellis", "Sara Gibson",
    "Janice McDonald", "Jean Cruz", "Kathryn Marshall", "Judy Ortiz", "Rose Gomez",
    "Beverly Murray", "Denise Freeman", "Marilyn Wells", "Amber Webb", "Danielle Simpson",
    "Brittany Stevens", "Diana Tucker", "Abigail Porter", "Natalie Hunter", "Sophia Hicks",
    "Isabella Crawford", "Charlotte Henry", "Mia Boyd", "Amelia Mason", "Harper Morales",
    "Evelyn Kennedy", "Ella Warren", "Madison Dixon", "Scarlett Ramos", "Grace Reyes",
    "Chloe Burns", "Victoria Gordon", "Riley Shaw", "Aria Holmes", "Lily Rice",
    "Aubrey Robertson", "Zoey Hunt", "Penelope Black", "Lillian Daniels", "Addison Palmer",
    
    # Additional names for diversity
    "Tyler Brooks", "Austin Russell", "Zachary Griffin", "Caleb Hayes", "Nathan Myers",
    "Isaac Ford", "Gavin Hamilton", "Landon Graham", "Christian Sullivan", "Isaiah Wallace",
    "Cameron Woods", "Hunter Cole", "Connor West", "Evan Jordan", "Adrian Owens",
    "Robert Reynolds", "Angel Fisher", "Jeremiah Ellis", "Miles Gibson", "Easton McDonald",
    "Nolan Cruz", "Blake Marshall", "Colton Ortiz", "Carson Gomez", "Cooper Murray",
    "Dominic Freeman", "Parker Wells", "Josiah Webb", "Adam Simpson", "Chase Stevens",
    "Jaxon Tucker", "Ian Porter", "Bentley Hunter", "Kayden Hicks", "Carson Crawford",
    "Brody Henry", "Asher Boyd", "Ezra Mason", "Xavier Morales", "Jace Kennedy",
    "Greyson Warren", "Silas Dixon", "Mateo Ramos", "Lincoln Reyes", "Maverick Burns",
    "Cole Gordon", "Brayden Shaw", "Sawyer Holmes", "Declan Rice", "Jameson Robertson",
    
    # More diverse female names
    "Avery Hunt", "Layla Black", "Zoe Daniels", "Bella Palmer", "Hannah Brooks",
    "Aaliyah Russell", "Ellie Griffin", "Leah Hayes", "Paisley Myers", "Nora Ford",
    "Hazel Hamilton", "Aurora Graham", "Savannah Sullivan", "Brooklyn Wallace", "Claire Woods",
    "Skylar Cole", "Lucy West", "Violet Jordan", "Genesis Owens", "Madelyn Reynolds",
    "Stella Fisher", "Audrey Ellis", "Alexa Gibson", "Piper McDonald", "Ruby Cruz",
    "Serenity Marshall", "Eva Ortiz", "Naomi Gomez", "Autumn Murray", "Quinn Freeman",
    "Willow Wells", "Nova Webb", "Ivy Simpson", "Elena Stevens", "Kennedy Tucker",
    "Emilia Porter", "Maya Hunter", "Melody Hicks", "Caroline Crawford", "Kinsley Henry",
    "Valentina Boyd", "Natalia Mason", "Alice Morales", "Delilah Kennedy", "Josephine Warren",
    "Isabelle Dixon", "Ariana Ramos", "Sophie Reyes", "Allison Burns", "Gabriella Gordon",
    "Sadie Shaw", "Anna Holmes", "Maria Rice", "Jasmine Robertson", "Iris Hunt",
    
    # Professional sounding names
    "Thomas Mitchell", "Richard Peterson", "Charles Richardson", "Christopher Cooper",
    "Daniel Bailey", "Matthew Turner", "Donald Phillips", "Mark Bennett", "Paul Wood",
    "Steven Ross", "Andrew Coleman", "Kenneth Jenkins", "Brian Howard", "George Ward",
    "Edward Torres", "Timothy Flores", "Ronald Butler", "Jason Washington", "Jeffrey Powell",
    "Ryan Long", "Jacob Patterson", "Gary Hughes", "Nicholas Sanders", "Eric Price",
    "Jonathan Perry", "Stephen Ramirez", "Larry James", "Justin Watson", "Scott Brooks",
    "Brandon Kelly", "Raymond Sanders", "Frank Bennett", "Benjamin Wood", "Gregory Ross",
    
    "Elizabeth Coleman", "Susan Jenkins", "Karen Howard", "Nancy Ward", "Lisa Torres",
    "Betty Flores", "Margaret Butler", "Sandra Washington", "Ashley Powell", "Kimberly Long",
    "Emily Patterson", "Donna Hughes", "Michelle Sanders", "Carol Price", "Amanda Perry",
    "Melissa Ramirez", "Deborah James", "Stephanie Watson", "Dorothy Brooks", "Rebecca Kelly",
    "Sharon Sanders", "Laura Bennett", "Cynthia Wood", "Amy Ross", "Kathleen Coleman",
    
    # Modern names
    "Liam Anderson", "Noah Johnson", "William Williams", "James Brown", "Oliver Jones",
    "Benjamin Garcia", "Elijah Martinez", "Lucas Rodriguez", "Mason Hernandez", "Logan Lopez",
    "Alexander Wilson", "Ethan Moore", "Jacob Taylor", "Michael Thomas", "Daniel Jackson",
    "Henry White", "Jackson Harris", "Sebastian Martin", "Aiden Thompson", "Matthew Garcia",
    "Samuel Martinez", "David Robinson", "Joseph Clark", "Carter Rodriguez", "Owen Lewis",
    "Wyatt Lee", "John Walker", "Jack Hall", "Luke Allen", "Jayden Young",
    "Dylan Hernandez", "Grayson King", "Levi Wright", "Isaac Lopez", "Gabriel Hill",
    
    "Emma Anderson", "Olivia Johnson", "Ava Williams", "Sophia Brown", "Isabella Jones",
    "Mia Garcia", "Charlotte Martinez", "Amelia Rodriguez", "Harper Hernandez", "Evelyn Lopez",
    "Abigail Wilson", "Emily Moore", "Ella Taylor", "Elizabeth Thomas", "Camila Jackson",
    "Luna White", "Sofia Harris", "Avery Martin", "Mila Thompson", "Aria Garcia",
    "Scarlett Martinez", "Penelope Robinson", "Layla Clark", "Chloe Rodriguez", "Victoria Lewis",
    "Madison Lee", "Eleanor Walker", "Grace Hall", "Nora Allen", "Riley Young",
    "Zoey Hernandez", "Hannah King", "Hazel Wright", "Lily Lopez", "Ellie Hill",
    
    # Classic American names
    "Frank Peterson", "George Richardson", "Harold Cooper", "Walter Bailey", "Arthur Turner",
    "Albert Phillips", "Eugene Bennett", "Carl Wood", "Howard Ross", "Lawrence Coleman",
    "Dennis Jenkins", "Ralph Howard", "Willie Ward", "Harry Torres", "Louis Flores",
    "Jack Butler", "Roy Washington", "Bobby Powell", "Joe Long", "Bruce Patterson",
    
    "Helen Hughes", "Martha Sanders", "Ruth Price", "Virginia Perry", "Doris Ramirez",
    "Frances James", "Evelyn Watson", "Marie Brooks", "Lillian Kelly", "Florence Sanders",
    "Ruby Bennett", "Gladys Wood", "Edna Ross", "Irene Coleman", "Mildred Jenkins",
    "Louise Howard", "Thelma Ward", "Edith Torres", "Ethel Flores", "Marjorie Butler",
    
    # Contemporary names
    "Jackson Miller", "Aiden Davis", "Lucas Garcia", "Liam Rodriguez", "Noah Martinez",
    "Mason Lopez", "Ethan Gonzalez", "Logan Wilson", "Oliver Anderson", "Elijah Taylor",
    "James Thomas", "William Moore", "Benjamin Jackson", "Henry Martin", "Alexander Lee",
    
    "Sophia Walker", "Emma Harris", "Olivia Clark", "Ava Lewis", "Isabella Robinson",
    "Mia Allen", "Charlotte Young", "Amelia King", "Harper Wright", "Evelyn Scott",
    "Abigail Green", "Emily Adams", "Ella Baker", "Elizabeth Nelson", "Sofia Carter",
    
    # Additional professional names
    "Patrick Murphy", "Sean Rivera", "Alan Cooper", "Terry Richardson", "Jesse Cox",
    "Gerald Howard", "Keith Ward", "Samuel Torres", "Martin Peterson", "Douglas Gray",
    "Russell Ramirez", "Vincent James", "Gregory Watson", "Kyle Brooks", "Jeremy Kelly",
    
    "Beverly Hughes", "Diane Sanders", "Alice Price", "Cheryl Perry", "Gloria Butler",
    "Teresa Washington", "Ann Powell", "Janice Long", "Kathryn Patterson", "Joyce Hughes"
]
