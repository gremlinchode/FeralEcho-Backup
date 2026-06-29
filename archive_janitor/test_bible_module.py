import bible_module as bible

# Test getting a verse
verse = bible.get_verse("Genesis", 1, 1)
print("Verse:", verse)

# Test most positive verse
positive = bible.get_most_positive_verse()
print("Most positive:", positive)

# Test most negative verse
negative = bible.get_most_negative_verse()
print("Most negative:", negative)

# Generate art
image_path = bible.generate_bible_art(reference="most_positive")
print("Art saved to:", image_path)
