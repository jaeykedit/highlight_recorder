// GoToMarkerOut.jsx
var project = app.project;
var sequence = project.activeSequence;
var markers = sequence.markers;

if (markers.numMarkers > 0) {
    var marker = markers.getFirstMarker(); // 또는 현재 플레이헤드 근처 마커 선택
    while (marker && marker.end > sequence.getPlayerPosition().seconds) {
        marker = markers.getNextMarker(marker);
    }
    if (marker && marker.end > 0) {
        sequence.setPlayerPosition(marker.end * 60); // 60fps 기준 프레임 단위
        alert("Moved to marker out point: " + marker.end);
    } else {
        alert("No valid marker out point found.");
    }
} else {
    alert("No markers in sequence.");
}