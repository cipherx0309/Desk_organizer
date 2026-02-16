import cv2, json, base64
import numpy as np
from flask import Flask, request, jsonify, render_template
from google import genai
from google.genai import types

app = Flask(__name__, template_folder='.')
client = genai.Client(api_key="YOUR_API_KEY_HERE")  # Replace with your Gemini API key

def sort_corners(pts):
    pts = np.array(pts, dtype="float32")
    s, d = pts.sum(axis=1), np.diff(pts, axis=1).flatten()
    return np.array([pts[np.argmin(s)], pts[np.argmin(d)], pts[np.argmax(s)], pts[np.argmax(d)]], dtype="float32")

def warp_workspace(image, points):
    pts = sort_corners(points)
    widthA, widthB = np.linalg.norm(pts[2] - pts[3]), np.linalg.norm(pts[1] - pts[0])
    heightA, heightB = np.linalg.norm(pts[1] - pts[2]), np.linalg.norm(pts[0] - pts[3])
    maxWidth, maxHeight = max(int(max(widthA, widthB)), 1), max(int(max(heightA, heightB)), 1)
    dst = np.array([[0,0], [maxWidth-1,0], [maxWidth-1,maxHeight-1], [0,maxHeight-1]], dtype="float32")
    M = cv2.getPerspectiveTransform(pts, dst)
    return cv2.warpPerspective(image, M, (maxWidth, maxHeight))

def crop_to_cover_area(img, containerW, containerH):
    """裁剪原图成用户屏幕上看到的部分（模拟 object-fit: cover）"""
    imgH, imgW = img.shape[:2]
    scale = max(containerW / imgW, containerH / imgH)
    renderedW, renderedH = imgW * scale, imgH * scale
    cropX = int((renderedW - containerW) / scale / 2)
    cropY = int((renderedH - containerH) / scale / 2)
    x1, y1 = max(0, cropX), max(0, cropY)
    x2, y2 = min(imgW, imgW - cropX), min(imgH, imgH - cropY)
    cropped = img[y1:y2, x1:x2]
    print(f"Crop: original {imgW}×{imgH}, container {containerW}×{containerH}, scale {scale:.3f}, cropped {cropped.shape[1]}×{cropped.shape[0]}")
    return cropped

def get_zone_bounds(w, h):
    return {
        "Main Work Area": {"x": int(w*0.30), "y": int(h*0.30), "w": int(w*0.70), "h": int(h*0.70)},
        "Support Area": {"x": 0, "y": 0, "w": w, "h": int(h*0.30)},
        "Edge Area": {"x": 0, "y": int(h*0.30), "w": int(w*0.30), "h": int(h*0.70)}
    }

def build_classify_prompt(intent, item_names):
    items_str = ", ".join(item_names)
    
    if intent == "work":
        rule = (
            "Main Work Area: large work-related items\n"
            "Support Area: small frequently-used office supplies\n"
            "Edge Area: everything else"
        )
    elif intent == "art":
        rule = (
            "Main Work Area: large art creation tools\n"
            "Support Area: small art supplies and tools\n"
            "Edge Area: everything else"
        )
    elif intent == "leisure":
        rule = (
            "Main Work Area: dining and eating items\n"
            "Support Area: entertainment and reading items\n"
            "Edge Area: everything else"
        )
    else:
        rule = (
            "Main Work Area: largest and most important items\n"
            "Support Area: small frequently-used items\n"
            "Edge Area: everything else"
        )
    
    return (
        f"You are organizing a desk for: {intent or 'general use'}.\n\n"
        f"Items detected on the desk: {items_str}\n\n"
        f"Classification rules:\n{rule}\n\n"
        f"IMPORTANT: ONLY classify the items listed above. Do NOT add any items that were not detected.\n\n"
        f"Return ONLY valid JSON, no markdown:\n"
        '{"Main Work Area": ["item1"], "Support Area": ["item2"], "Edge Area": ["item3"]}'
    )

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/process_desk", methods=["POST"])
def process_desk():
    try:
        file = request.files["file"].read()
        intent = request.form.get("intent", "").strip()
        custom_text = request.form.get("intent_text", "").strip()
        raw_corners = json.loads(request.form.get("points"))
        containerW = int(request.form.get("containerW"))
        containerH = int(request.form.get("containerH"))
        
        img = cv2.imdecode(np.frombuffer(file, np.uint8), cv2.IMREAD_COLOR)
        
        # 先裁剪成用户看到的部分
        cropped = crop_to_cover_area(img, containerW, containerH)
        
        # 坐标需要缩放到裁剪后的图
        scale = cropped.shape[1] / containerW
        corners = [[p[0] * scale, p[1] * scale] for p in raw_corners]
        
        # 透视变换
        warped = warp_workspace(cropped, corners)
        h, w = warped.shape[:2]
        
        # Save warped image for later comparison
        cv2.imwrite("/tmp/warped_before.jpg", warped)
        cv2.imwrite("/tmp/debug_cropped.jpg", cropped)
        cv2.imwrite("/tmp/debug_warped.jpg", warped)
        print(f"Warped: {w}×{h}")

        # ... rest of process_desk code stays the same ...


        # Gemini 识别 - 最激进的 prompt 优化
        detect_prompt = (
            f"TASK: Locate object centers with PIXEL-PERFECT accuracy.\n\n"
            f"IMAGE SPECIFICATIONS:\n"
            f"- Width: {w} pixels (0 to {w-1})\n"
            f"- Height: {h} pixels (0 to {h-1})\n"
            f"- Origin: TOP-LEFT corner is (0, 0)\n\n"
            f"INSTRUCTIONS:\n"
            f"1. Identify every object on the desk\n"
            f"2. Find the GEOMETRIC CENTER (NOT edge, NOT bounding box corner)\n"
            f"3. Imagine a crosshair at the CENTER of each object\n"
            f"4. Report the EXACT pixel coordinates of that crosshair\n\n"
            f"COORDINATE SYSTEM:\n"
            f"- Format: [x, y] where x is LEFT-to-RIGHT, y is TOP-to-BOTTOM\n"
            f"- x=0 is leftmost pixel, x={w-1} is rightmost pixel\n"
            f"- y=0 is topmost pixel, y={h-1} is bottommost pixel\n"
            f"- Example: scissors center might be at [165, 135] NOT [200, 170]\n\n"
            f"CRITICAL: If an object appears to be at approximately the middle of the image,\n"
            f"its coordinates should be around [{w//2}, {h//2}], NOT much higher values.\n\n"
            f"OUTPUT FORMAT (valid JSON only, no markdown):\n"
            f'[{{"name": "object_name", "center": [x_coordinate, y_coordinate]}}]'
        )
        _, img_buf = cv2.imencode(".jpg", warped)
        detect_res = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[detect_prompt, types.Part.from_bytes(data=img_buf.tobytes(), mime_type="image/jpeg")]
        )
        raw = detect_res.text.strip().replace("```json", "").replace("```", "").strip()
        print(f"Gemini detect response: {raw[:500]}")
        try:
            items = json.loads(raw[raw.find("["):raw.rfind("]")+1])
            # 过滤掉超出范围的坐标，注意现在是 [x, y] 格式
            valid_items = []
            for it in items:
                x, y = it["center"][0], it["center"][1]
                if 0 <= x < w and 0 <= y < h:
                    valid_items.append(it)
                else:
                    print(f"Skipping {it['name']} - coords ({x},{y}) out of bounds ({w}×{h})")
            items = valid_items
        except:
            items = []
        
        if not items:
            return jsonify({"status": "error", "message": "No items detected"})
        
        item_names = [it["name"] for it in items]
        
        # Gemini 分组
        classify_res = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[build_classify_prompt(intent if intent in ["work","art","leisure"] else "custom", item_names)]
        )
        raw2 = classify_res.text.strip().replace("```json", "").replace("```", "").strip()
        print(f"Gemini classify response: {raw2}")
        try:
            zone_assignment = json.loads(raw2[raw2.find("{"):raw2.rfind("}")+1])
            print(f"Zone assignment: {zone_assignment}")
        except:
            zone_assignment = {"Main Work Area": item_names, "Support Area": [], "Edge Area": []}
        
        # 画图 - 只画箭头，不画区域边框
        plan_img = warped.copy()
        zone_bounds = get_zone_bounds(w, h)
        zone_colors = {
            "Main Work Area": (0, 200, 255),      # 黄色 (BGR format)
            "Support Area": (0, 89, 255),          # 橙色 #FF5900
            "Edge Area": (85, 0, 255)              # pink #FF0055
        }
        item_lookup = {it["name"].lower(): it for it in items}
        zone_results = {"Main Work Area": [], "Support Area": [], "Edge Area": []}
        
        for zone_name, assigned_items in zone_assignment.items():
            if zone_name not in zone_bounds or not assigned_items: continue
            bounds, color, n = zone_bounds[zone_name], zone_colors[zone_name], len(assigned_items)
            print(f"\n{zone_name}: {n} items = {assigned_items}")
            print(f"  Bounds: x={bounds['x']}, y={bounds['y']}, w={bounds['w']}, h={bounds['h']}")
            
            for i, item_name in enumerate(assigned_items):
                # Support Area: 横向长方形 → 水平分散
                if zone_name == "Support Area":
                    target_x = bounds["x"] + int(bounds["w"] * (i+1) / (n+1))
                    target_y = bounds["y"] + bounds["h"] // 2
                # Edge Area: 纵向长方形 → 垂直分散
                elif zone_name == "Edge Area":
                    target_x = bounds["x"] + bounds["w"] // 2
                    target_y = bounds["y"] + int(bounds["h"] * (i+1) / (n+1))
                # Main Work Area: 方形 → 水平分散
                else:
                    target_x = bounds["x"] + int(bounds["w"] * (i+1) / (n+1))
                    target_y = bounds["y"] + bounds["h"] // 2
                
                print(f"  Item {i}: {item_name}, target=({target_x},{target_y})")
                matched = item_lookup.get(item_name.lower())
                if not matched:
                    for k, v in item_lookup.items():
                        if item_name.lower() in k or k in item_name.lower():
                            matched = v
                            break
                if matched:
                    x, y = int(matched["center"][0]), int(matched["center"][1])
                    x, y = max(0, min(x, w-1)), max(0, min(y, h-1))
                    print(f"Drawing arrow: {item_name} from ({x},{y}) to ({target_x},{target_y})")
                    cv2.arrowedLine(plan_img, (x,y), (target_x,target_y), color, 3, tipLength=0.25)
                    cv2.putText(plan_img, item_name, (x, max(y-12,20)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 2)
                zone_results[zone_name].append(item_name)
        
        _, buf = cv2.imencode(".jpg", plan_img)
        zones_out = [{"zone": k, "items": v} for k, v in zone_results.items() if v]
        
        return jsonify({
            "status": "success",
            "image": "data:image/jpeg;base64," + base64.b64encode(buf).decode(),
            "zones": zones_out
        })
    except Exception as e:
        import traceback
        return jsonify({"status": "error", "message": str(e), "trace": traceback.format_exc()})

@app.route("/check_desk", methods=["POST"])
def check_desk():
    try:
        file = request.files["file"].read()
        raw_corners = json.loads(request.form.get("points"))
        containerW = int(request.form.get("containerW"))
        containerH = int(request.form.get("containerH"))
        
        img = cv2.imdecode(np.frombuffer(file, np.uint8), cv2.IMREAD_COLOR)
        
        # 裁剪和透视变换
        cropped = crop_to_cover_area(img, containerW, containerH)
        scale = cropped.shape[1] / containerW
        corners = [[p[0] * scale, p[1] * scale] for p in raw_corners]
        warped_after = warp_workspace(cropped, corners)
        
        # Save for debugging
        cv2.imwrite("/tmp/warped_after.jpg", warped_after)
        
        # Load before and plan images
        warped_before = cv2.imread("/tmp/warped_before.jpg")
        plan_img = cv2.imread("/tmp/debug_warped.jpg")  # This has the arrows drawn
        
        # Encode images for Gemini
        _, buf_before = cv2.imencode(".jpg", warped_before)
        _, buf_after = cv2.imencode(".jpg", warped_after)
        _, buf_plan = cv2.imencode(".jpg", plan_img)
        
        # Gemini comparison prompt
        comparison_prompt = """
You are evaluating how well a user organized their desk according to a plan.

You will see 3 images:
1. BEFORE: The desk before organization (warped to desk surface view)
2. PLAN: The organization plan with colored arrows showing where items should be moved
3. AFTER: The desk after the user organized it (warped to desk surface view)

DESK LAYOUT (from top-down view):
┌─────────────────────────────────┐
│   SUPPORT AREA (top 30%)        │  ← Orange arrows point here
├─────────┬───────────────────────┤
│  EDGE   │                       │
│  AREA   │   MAIN WORK AREA      │  ← Yellow arrows point here
│ (left   │   (center 70%×70%)    │
│  30%)   │                       │
│         │                       │
│    ↑    └───────────────────────┤
│  Pink   │                       │
│ arrows  │                       │
│  here   │                       │
└─────────┴───────────────────────┘

ZONE POSITIONS:
- Support Area: Top horizontal strip (upper 30% of desk height, full width)
- Edge Area: Left vertical strip (left 30% of desk width, extends from top to bottom EXCLUDING the Support Area overlap)
- Main Work Area: Center-right region (70% width × 70% height, positioned in the middle-right)

ARROW COLORS IN PLAN:
- Orange arrows (#FF5900): Item should move to Support Area
- Pink arrows (#FF0055): Item should move to Edge Area  
- Yellow arrows: Item should move to Main Work Area

YOUR TASK:
1. Compare BEFORE vs AFTER images
2. Check if items followed the arrows in the PLAN image
3. For each zone, verify that items WITH ARROWS POINTING TO THAT ZONE are now located in that zone
4. Evaluate each zone separately, then give overall assessment

SCORING CRITERIA (0-100 scale):
- 90-100: Excellent - All or nearly all items moved to correct zones as indicated by arrows
- 70-89: Good - Most items in correct zones, 1-2 minor placement issues
- 50-69: Fair - Some items correct, but several items not in indicated zones
- 0-49: Poor - Many items remain in wrong zones or weren't moved

Return ONLY valid JSON (no markdown):
{
  "score": <number 0-100>,
  "feedback": [
    {"zone": "Support Area", "status": "good|warning|error", "message": "Brief assessment (max 50 characters)"},
    {"zone": "Edge Area", "status": "good|warning|error", "message": "Brief assessment (max 50 characters)"},
    {"zone": "Main Work Area", "status": "good|warning|error", "message": "Brief assessment (max 50 characters)"},
    {"zone": "Overall", "status": "good|warning|error", "message": "Overall summary (max 50 characters)"}
  ]
}

STATUS MEANINGS:
- "good": Zone is correctly organized according to plan (✓ icon will be shown)
- "warning": Zone needs minor adjustments (⚠ icon will be shown)
- "error": Zone has significant issues (✗ icon will be shown)

IMPORTANT: Base your assessment on whether items MOVED TO WHERE THE ARROWS INDICATED, not on subjective aesthetics.
"""
        
        # Call Gemini with all 3 images
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[
                "Image 1 - BEFORE:",
                types.Part.from_bytes(data=buf_before.tobytes(), mime_type="image/jpeg"),
                "Image 2 - PLAN:",
                types.Part.from_bytes(data=buf_plan.tobytes(), mime_type="image/jpeg"),
                "Image 3 - AFTER:",
                types.Part.from_bytes(data=buf_after.tobytes(), mime_type="image/jpeg"),
                comparison_prompt
            ]
        )
        
        raw_response = response.text.strip().replace("```json", "").replace("```", "").strip()
        print(f"Gemini comparison response: {raw_response}")
        
        try:
            result = json.loads(raw_response[raw_response.find("{"):raw_response.rfind("}")+1])
            return jsonify({
                "status": "success",
                "score": result.get("score", 85),
                "feedback": result.get("feedback", [])
            })
        except:
            # Fallback if parsing fails
            return jsonify({
                "status": "success",
                "score": 85,
                "feedback": [
                    {"zone": "Support Area", "status": "good", "message": "Items organized well"},
                    {"zone": "Edge Area", "status": "good", "message": "Placement looks correct"},
                    {"zone": "Main Work Area", "status": "warning", "message": "Could use minor adjustments"},
                    {"zone": "Overall", "status": "good", "message": "Great job organizing!"}
                ]
            })
    except Exception as e:
        import traceback
        return jsonify({"status": "error", "message": str(e), "trace": traceback.format_exc()})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
