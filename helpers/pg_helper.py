## MISC FUNCTIONS

def replace_text(slide, old_text, new_text):
    for shape in slide.shapes:
        if shape.has_text_frame:
            for p in shape.text_frame.paragraphs:
                og_alignment = p.alignment
                for run in p.runs:
                    og_font_name = run.font.name
                    og_font_size = run.font.size
                    og_font_bold = run.font.bold
                    og_font_italic = run.font.italic
                    if f"#{old_text}" in run.text:
                        run.text = run.text.replace(f"#{old_text}", new_text)
                    run.font.name = og_font_name
                    run.font.size = og_font_size
                    run.font.bold = og_font_bold
                    run.font.italic = og_font_italic
                p.alignment = og_alignment
        elif shape.has_table:
            for cell in shape.table.iter_cells():
                for p in cell.text_frame.paragraphs:
                    og_alignment = p.alignment
                    for run in p.runs:
                        og_font_name = run.font.name
                        og_font_size = run.font.size
                        og_font_bold = run.font.bold
                        og_font_italic = run.font.italic
                        if f"#{old_text}" in run.text:
                            run.text = run.text.replace(f"#{old_text}", new_text)
                        run.font.name = og_font_name
                        run.font.size = og_font_size
                        run.font.bold = og_font_bold
                        run.font.italic = og_font_italic
                    p.alignment = og_alignment

def delete_slide(presentation, index):
    """Deletes a slide from the presentation by its index."""
    # Ensure the index is valid
    if not (0 <= index < len(presentation.slides)):
        raise IndexError("Slide index out of bounds")

    # Get the slide ID and relationship ID
    slide_id = presentation.slides._sldIdLst[index].rId

    # Drop the relationship to the slide part
    presentation.part.drop_rel(slide_id)

    # Remove the slide ID from the slide list
    del presentation.slides._sldIdLst[index]

def abbreviate_number(number):
    if not isinstance(number, (int, float)):
        raise TypeError("Input must be an integer or a float.")
    if number < 1000:
        return str(number)
    suffixes = ["K", "M", "B", "T", "Q"]
    divisor = 1000.0
    index = -1
    while abs(number) >= divisor and index < len(suffixes) - 1:
        number /= divisor
        index += 1
    if number % 1 == 0:
        return f"{int(number)}{suffixes[index]}"
    else:
        return f"{number:.1f}{suffixes[index]}"

def ordinal(n: int) -> str:
    if 11 <= (n % 100) <= 13:
        suffix = 'th'
    else:
        suffix = ['th', 'st', 'nd', 'rd', 'th'][min(n % 10, 4)]
    return str(n) + suffix

def find_shape_by_name(slide, shape_name):
    for shape in slide.shapes:
        if shape.name == shape_name:
            return shape
    return None

def range_calculator(final_chart:list, start:int, end:int, metric:str):
    final_value = 0
    for x in final_chart[start:end]:
        final_value += x[metric]
    return final_value