
// ============================================================
// SMART ATTENDANCE SYSTEM
// Dashboard JavaScript
// ============================================================


// ------------------------------------------------------------
// 1. GLOBAL VARIABLES AND HELPER FUNCTIONS
// ------------------------------------------------------------

// Get an HTML element by its ID.
function getElement(id) {
    return document.getElementById(id);
}

// Get the CSRF token from Flask.
const csrfToken = window.DASH_CONFIG.csrf;

// Selected course.
const courseSelect = getElement("course");

// Webcam stream used for face registration.
let cameraStream = null;

// Tracks whether a possible duplicate face was detected.
let possibleDuplicate = false;


// ------------------------------------------------------------
// 2. DISPLAY CURRENT DATE
// ------------------------------------------------------------

function displayCurrentDate() {
    const currentDate = new Date();

    const formattedDate = currentDate.toLocaleDateString(
        undefined,
        {
            weekday: "short",
            month: "short",
            day: "numeric"
        }
    );

    getElement("clock").textContent = formattedDate;
}


// ------------------------------------------------------------
// 3. SEND POST REQUESTS TO FLASK
// ------------------------------------------------------------

async function post(url, payload = {}) {
    const response = await fetch(url, {
        method: "POST",

        headers: {
            "Content-Type": "application/json",
            "X-CSRF-Token": csrfToken
        },

        body: JSON.stringify(payload)
    });

    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
        throw new Error(data.error || "Request failed");
    }

    return data;
}


// ------------------------------------------------------------
// 4. UPDATE FACE RECOGNITION SESSION STATUS
// ------------------------------------------------------------

async function updateSession() {
    try {
        const response = await fetch("/api/attendance-session");

        if (!response.ok) {
            throw new Error("Unable to check session");
        }

        const data = await response.json();

        const cameraBadge = getElement("cameraBadge");
        const sessionLabel = getElement("sessionLabel");
        const startButton = getElement("startCamera");

        if (data.active) {
            cameraBadge.textContent = "● Running";
            cameraBadge.classList.add("running");

            sessionLabel.textContent = "Active";

            startButton.disabled = true;

            getElement("checkinState").textContent =
                "Camera session active";

            getElement("checkinInfo").textContent =
                "Complete verification in the camera window";
        } else {
            cameraBadge.textContent = "● Ready";
            cameraBadge.classList.remove("running");

            sessionLabel.textContent = "Idle";

            startButton.disabled = false;
        }

    } catch (error) {
        getElement("sessionLabel").textContent = "Offline";
    }
}


// ------------------------------------------------------------
// 5. UPDATE ATTENDANCE RECORDS
// ------------------------------------------------------------

async function updateAttendance() {
    const selectedCourse = courseSelect.value;

    // Update the CSV export link.
    getElement("exportCsv").href =
        "/reports?course=" +
        encodeURIComponent(selectedCourse) +
        "&format=csv";

    try {
        const response = await fetch(
            "/api/attendance/" + encodeURIComponent(selectedCourse)
        );

        const attendanceRecords = await response.json();

        if (!response.ok) {
            throw new Error(
                attendanceRecords.error || "Unable to load attendance"
            );
        }

        // Get today's local date.
        const today = new Date();

        const localDate = [
            today.getFullYear(),
            String(today.getMonth() + 1).padStart(2, "0"),
            String(today.getDate()).padStart(2, "0")
        ].join("-");

        // Count students marked Present or Late today.
        const todayAttendance = attendanceRecords.filter((record) => {
            const attendanceDate = record[1];
            const attendanceStatus = record[3];

            return (
                attendanceDate === localDate &&
                ["Present", "Late"].includes(attendanceStatus)
            );
        });

        getElement("todayCount").textContent =
            todayAttendance.length;

        // Clear the previous attendance table.
        const tableBody = getElement("attendanceRows");

        tableBody.replaceChildren();

        // Display a message if no attendance records exist.
        if (attendanceRecords.length === 0) {
            const tableRow = document.createElement("tr");
            const tableCell = document.createElement("td");

            tableCell.colSpan = 3;
            tableCell.textContent =
                "No check-ins for this course yet.";

            tableRow.appendChild(tableCell);
            tableBody.appendChild(tableRow);

            return;
        }

        // Display the latest seven records.
        const recentRecords = attendanceRecords.slice(0, 7);

        for (const record of recentRecords) {
            const tableRow = document.createElement("tr");

            const studentName = record[0];
            const dateAndTime = record[1] + " · " + record[2];
            const attendanceStatus = record[3];

            const values = [
                studentName,
                dateAndTime,
                attendanceStatus
            ];

            for (const value of values) {
                const tableCell = document.createElement("td");

                tableCell.textContent = value;

                tableRow.appendChild(tableCell);
            }

            tableBody.appendChild(tableRow);
        }

        getElement("attendanceMsg").textContent = "";

    } catch (error) {
        getElement("attendanceMsg").textContent = error.message;
    }
}


// ------------------------------------------------------------
// 6. START FACE RECOGNITION
// ------------------------------------------------------------

async function startFaceRecognition() {
    const selectedCourse = courseSelect.value;

    getElement("recognitionMsg").textContent =
        "Launching camera...";

    try {
        const data = await post(
            "/api/start-attendance/" + encodeURIComponent(selectedCourse)
        );

        getElement("recognitionMsg").textContent =
            data.message || "Camera started";

        await updateSession();

    } catch (error) {
        getElement("recognitionMsg").textContent = error.message;
    }
}


// ------------------------------------------------------------
// 7. SEARCH STUDENTS
// ------------------------------------------------------------

function searchStudents(event) {
    const searchText = event.target.value
        .toLowerCase()
        .trim();

    const studentRows = document.querySelectorAll(
        "#studentRows tr[data-search]"
    );

    studentRows.forEach((row) => {
        const studentInformation = row.dataset.search || "";

        row.hidden = !studentInformation.includes(searchText);
    });
}


// ------------------------------------------------------------
// 8. SHOW OR HIDE FACE REGISTRATION
// ------------------------------------------------------------

function toggleRegistration() {
    const registrationSection = getElement("registration");
    const toggleButton = getElement("toggleRegister");

    registrationSection.hidden = !registrationSection.hidden;

    if (registrationSection.hidden) {
        toggleButton.textContent = "＋ Register Face";
    } else {
        toggleButton.textContent = "Close Registration";
    }
}


// ------------------------------------------------------------
// 9. CAPTURE AN IMAGE FROM THE WEBCAM
// ------------------------------------------------------------

function captureFaceImage() {
    const canvas = getElement("canvas");
    const video = getElement("video");

    const context = canvas.getContext("2d");

    context.drawImage(
        video,
        0,
        0,
        480,
        360
    );

    return canvas.toDataURL("image/jpeg", 0.7);
}


// ------------------------------------------------------------
// 10. ENABLE CAMERA FOR FACE REGISTRATION
// ------------------------------------------------------------

async function enableRegistrationCamera() {
    try {
        // Stop an existing stream before opening a new one.
        if (cameraStream) {
            cameraStream.getTracks().forEach((track) => {
                track.stop();
            });
        }

        cameraStream = await navigator.mediaDevices.getUserMedia({
            video: true,
            audio: false
        });

        const video = getElement("video");

        video.srcObject = cameraStream;

        await video.play();

        getElement("checkFace").disabled = false;
        getElement("saveFace").disabled = false;

        getElement("registrationMsg").textContent =
            "Camera ready";

    } catch (error) {
        getElement("registrationMsg").textContent =
            "Camera unavailable: " + error.message;
    }
}


// ------------------------------------------------------------
// 11. DISPLAY POSSIBLE DUPLICATE FACE WARNING
// ------------------------------------------------------------

function showDuplicateWarning(match) {
    possibleDuplicate = true;

    getElement("duplicateWarning").hidden = false;

    getElement("matchText").textContent =
        `Possible match: ${match.name} ` +
        `(${match.student_id}), ` +
        `LBPH distance ${match.distance}. ` +
        "Verify the student ID.";
}


// ------------------------------------------------------------
// 12. CHECK FOR AN EXISTING FACE
// ------------------------------------------------------------

async function checkDuplicateFace() {
    try {
        const image = captureFaceImage();

        const data = await post(
            "/api/registration/check",
            {
                image: image
            }
        );

        if (data.possible_match) {
            showDuplicateWarning(data.possible_match);

        } else {
            possibleDuplicate = false;

            getElement("duplicateWarning").hidden = true;

            getElement("registrationMsg").textContent =
                "No likely duplicate found";
        }

    } catch (error) {
        getElement("registrationMsg").textContent = error.message;
    }
}


// ------------------------------------------------------------
// 13. REGISTER A STUDENT'S FACE
// ------------------------------------------------------------

async function registerStudentFace() {
    const studentId = getElement("sid").value.trim();
    const studentName = getElement("studentName").value.trim();

    const registrationMessage = getElement("registrationMsg");
    const saveButton = getElement("saveFace");

    // Validate the student ID and name.
    if (!/^\d+$/.test(studentId) || !studentName) {
        registrationMessage.textContent =
            "Enter a numeric ID and name";

        return;
    }

    // Require duplicate review when a possible match exists.
    if (possibleDuplicate && !getElement("override").checked) {
        registrationMessage.textContent =
            "Review the duplicate warning first";

        return;
    }

    saveButton.disabled = true;

    try {
        const images = [];

        // Capture 30 facial images.
        for (let index = 0; index < 30; index++) {
            const image = captureFaceImage();

            images.push(image);

            registrationMessage.textContent =
                `Capturing ${index + 1} / 30`;

            // Wait briefly between captures.
            await new Promise((resolve) => {
                setTimeout(resolve, 180);
            });
        }

        // Send registration data to Flask.
        const data = await post(
            "/api/registration/save",
            {
                student_id: studentId,
                name: studentName,
                images: images,

                reviewed_possible_match:
                    possibleDuplicate &&
                    getElement("override").checked
            }
        );

        registrationMessage.textContent =
            data.message + " — refreshing...";

        window.location.reload();

    } catch (error) {
        if (
            error.message.includes(
                "Possible existing registration"
            )
        ) {
            registrationMessage.textContent =
                "Possible duplicate. Use Check Duplicate " +
                "and review before proceeding.";

        } else {
            registrationMessage.textContent = error.message;
        }

    } finally {
        saveButton.disabled = false;
    }
}


// ------------------------------------------------------------
// 14. DELETE A STUDENT
// ------------------------------------------------------------

async function deleteStudent(button) {
    const studentId = button.dataset.id;
    const studentName = button.dataset.name;

    // Ask for confirmation before permanent deletion.
    const confirmed = window.confirm(
        `Permanently delete ${studentName} (${studentId})?\n\n` +
        "This removes attendance history and face samples."
    );

    if (!confirmed) {
        return;
    }

    button.disabled = true;

    try {
        // Send the deletion request to Flask.
        await post(
            "/api/students/" +
            encodeURIComponent(studentId) +
            "/delete",
            {
                confirm: studentId
            }
        );

        // Reload the dashboard after successful deletion.
        window.location.reload();

    } catch (error) {
        window.alert(error.message);

        button.disabled = false;
    }
}


// ------------------------------------------------------------
// 15. STOP THE REGISTRATION CAMERA
// ------------------------------------------------------------

function stopRegistrationCamera() {
    if (cameraStream) {
        cameraStream.getTracks().forEach((track) => {
            track.stop();
        });

        cameraStream = null;
    }
}


// ------------------------------------------------------------
// 16. CONNECT BUTTONS TO THEIR FUNCTIONS
// ------------------------------------------------------------

// Update attendance when the selected course changes.
courseSelect.addEventListener(
    "change",
    updateAttendance
);

// Start facial recognition.
getElement("startCamera").addEventListener(
    "click",
    startFaceRecognition
);

// Search for students.
getElement("studentSearch").addEventListener(
    "input",
    searchStudents
);

// Show or hide the registration section.
getElement("toggleRegister").addEventListener(
    "click",
    toggleRegistration
);

// Enable the webcam for face registration.
getElement("enableCamera").addEventListener(
    "click",
    enableRegistrationCamera
);

// Check for possible duplicate registrations.
getElement("checkFace").addEventListener(
    "click",
    checkDuplicateFace
);

// Register a student's face.
getElement("saveFace").addEventListener(
    "click",
    registerStudentFace
);

// Connect each Delete button to the deletion function.
document.querySelectorAll(".delete-btn").forEach((button) => {
    button.addEventListener("click", () => {
        deleteStudent(button);
    });
});

// Release the webcam when leaving the page.
window.addEventListener(
    "pagehide",
    stopRegistrationCamera
);


// ------------------------------------------------------------
// 17. INITIALIZE THE DASHBOARD
// ------------------------------------------------------------

// Display the current date.
displayCurrentDate();

// Load the initial camera session status.
updateSession();

// Load the initial attendance records.
updateAttendance();

// Refresh attendance and camera status every 10 seconds.
setInterval(() => {
    updateSession();
    updateAttendance();
}, 10000);
