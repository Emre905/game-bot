import cv2
import numpy as np
import os

def find_x_button(image_path: str, debug: bool = False, debug_dir: str = "debug") -> tuple[int, int] | None:
    """
    Given a screenshot in "image_path", return coordinates of X button, if exists. If there's no X button, return None.
    Method:
    - Color Mask (HSV): Converts the crop to HSV and creates a binary mask targeting the specific bright red of the button (Hue near 0/180, Saturation ≥ 100).
    - Dilation: Applies a dilation filter to expand the white pixels in the mask, fusing the red corners into one solid, connected shape (filling the gaps left by the white "X").
    - Contour Filter: Finds all shapes in the mask, selects the largest one, and checks that its area is large enough (≥ 1000 px) to reject noise.
    - Center of Mass: Uses image moments (cv2.moments) on the chosen shape to calculate its exact geometric center, returning the full-screen (x, y) coordinate for the bot to tap. 
    """

    img = cv2.imread(image_path)
    if img is None:
        return None

    H, W = img.shape[:2]

    # 1. Crop the top-right corner 7% x 15% region (where the X button lives)
    x_start, y_start = int(W * 0.93), 0
    x_end,   y_end   = W, int(H * 0.12)
    roi = img[y_start:y_end, x_start:x_end]

    # 2. Convert to HSV and mask for red (since X button consists of red and white)
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    print("H, S, V:", hsv[50, 50]) 
    lower_red1 = np.array([0,   120, 120])
    upper_red1 = np.array([10,  255, 255])
    lower_red2 = np.array([170, 150, 150])
    upper_red2 = np.array([180, 255, 255])
    mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
    mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
    mask  = mask1 + mask2

    # 3. Find contours
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    result = None
    chosen = None

    if contours:
        # 4. Pick the largest red blob
        largest = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(largest)
        if area >= 200:
            # 5. Bounding box -> center, mapped back to full-screen coords
            x, y, w, h = cv2.boundingRect(largest)
            # sanity check: should be roughly square (the X button is square)
            if 0.85 <= w / max(h, 1) <= 1.4:
                chosen = (x, y, w, h)
                center_x = x_start + x + w // 2
                center_y = y_start + y + h // 2
                result = (center_x, center_y)

    # ---------------------------------------------------------------
    # Debug output
    # ---------------------------------------------------------------
    if debug:
        os.makedirs(debug_dir, exist_ok=True)

        # 1. Full screen with the ROI highlighted
        roi_dbg = img.copy()
        cv2.rectangle(roi_dbg, (x_start, y_start), (x_end, y_end), (0, 255, 255), 3)
        cv2.putText(roi_dbg, "ROI", (x_start + 10, y_start + 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 255), 2)
        cv2.imwrite(f"{debug_dir}/1_roi.png", roi_dbg)

        # 2. The cropped ROI itself
        cv2.imwrite(f"{debug_dir}/2_roi_crop.png", roi)

        # 3. ROI in HSV (as BGR so OpenCV can write it)
        cv2.imwrite(f"{debug_dir}/3_roi_hsv.png", cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR))

        # 4. Mask before and after combining red ranges
        cv2.imwrite(f"{debug_dir}/4_mask_low_red.png",  mask1)
        cv2.imwrite(f"{debug_dir}/4_mask_high_red.png", mask2)
        cv2.imwrite(f"{debug_dir}/4_mask_combined.png", mask)

        # 5. All contours drawn on the ROI
        contours_dbg = roi.copy()
        cv2.drawContours(contours_dbg, contours, -1, (0, 255, 0), 1)
        cv2.imwrite(f"{debug_dir}/5_all_contours.png", contours_dbg)

        # 6. Final: chosen box + center + score info
        final_dbg = img.copy()
        # draw every contour in yellow first (light)
        for c in contours:
            cx, cy, cw, ch = cv2.boundingRect(c)
            cv2.rectangle(final_dbg,
                          (x_start + cx, y_start + cy),
                          (x_start + cx + cw, y_start + cy + ch),
                          (0, 255, 255), 1)
        if chosen:
            x, y, w, h = chosen
            cx_roi, cy_roi = x + w // 2, y + h // 2
            center_hsv = hsv[cy_roi, cx_roi]
            print(f"Button center HSV: {center_hsv}")
            cv2.rectangle(final_dbg,
                          (x_start + x, y_start + y),
                          (x_start + x + w, y_start + y + h),
                          (0, 255, 0), 3)
            cv2.circle(final_dbg, result, 6, (255, 0, 255), -1)
            cv2.putText(final_dbg,
                        f"area={int(area)} box={w}x{h} ratio={w/max(h,1):.2f}",
                        (x_start, y_start + h + 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.imwrite(f"{debug_dir}/6_final.png", final_dbg)

        # 7. Side-by-side: ROI crop | mask | final
        roi_vis = roi.copy()
        mask_bgr = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
        final_crop = final_dbg[y_start:y_end, x_start:x_end]
        h_max = max(roi_vis.shape[0], mask_bgr.shape[0], final_crop.shape[0])
        def pad(im):
            return cv2.copyMakeBorder(im, 0, h_max - im.shape[0], 0, 10,
                                      cv2.BORDER_CONSTANT, value=(40, 40, 40))
        side_by_side = np.hstack([pad(roi_vis), pad(mask_bgr), pad(final_crop)])
        cv2.imwrite(f"{debug_dir}/7_side_by_side.png", side_by_side)

        print(f"[debug] saved 7 stages to {debug_dir}/")
        if chosen:
            x, y, w, h = chosen
            print(f"  chosen: box={w}x{h}  area={int(area)}  ratio={w/max(h,1):.2f}")
            print(f"  center: {result}")
            print(f"  total contours: {len(contours)}")
            # print sizes of all contours for tuning
            sizes = sorted([cv2.contourArea(c) for c in contours], reverse=True)[:5]
            print(f"  top-5 contour areas: {[int(s) for s in sizes]}")
        else:
            print(f"  no button matched. contours found: {len(contours)}")
            if contours:
                sizes = sorted([cv2.contourArea(c) for c in contours], reverse=True)[:5]
                print(f"  top-5 contour areas: {[int(s) for s in sizes]}")

    return result


if __name__ == "__main__":
    pos = find_x_button("debug/file.png", debug=True)
    print("X button at:", pos)
    print(type(pos))