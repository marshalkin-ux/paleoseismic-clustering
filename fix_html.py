with open('presentation/project_showcase.html', encoding='utf-8') as f:
    content = f.read()

# Find the proper end: </body>\n</html>\n
# The content after </html> is orphaned SEISMIC_EVENTS data
# Truncate at the first </body>\n</html>
end_marker = '</body>\n</html>\n'
idx = content.find(end_marker)
if idx != -1:
    content = content[:idx + len(end_marker)]
    print(f"Truncated at index {idx}")
else:
    # Try without trailing newline
    end_marker2 = '</body>\n</html>'
    idx2 = content.find(end_marker2)
    if idx2 != -1:
        content = content[:idx2 + len(end_marker2)] + '\n'
        print(f"Truncated at index {idx2}")
    else:
        print("END MARKER NOT FOUND")

with open('presentation/project_showcase.html', 'w', encoding='utf-8') as f:
    f.write(content)

print(f"Final size: {len(content.encode('utf-8'))} bytes")
print("Done")
