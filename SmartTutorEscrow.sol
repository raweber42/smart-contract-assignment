// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title SmartTutorEscrow
/// @notice MVP escrow contract for the Smart Contract Tutoring project (UZH FinTech & InsurTech HS 2025)
/// @dev This contract is simplified.

contract SmartTutorEscrow {
    /// @notice Status values for the lifecycle of a lesson
    enum LessonStatus {
        Created,          // lesson created, not funded yet
        Funded,           // funds are locked in escrow
        ResolvedPaid,     // funds paid to teacher + platform fee
        ResolvedRefunded, // funds refunded to student
        Cancelled         // lesson cancelled before funding
    }

    /// @notice On-chain representation of a single tutoring lesson
    struct Lesson {
        address payable student;       // wallet of the student (payer)
        address payable teacher;       // wallet of the teacher (receiver)
        uint256 lessonPrice;           // amount intended for the teacher (in MATIC)
        uint256 platformFee;           // fee for the platform (in MATIC)
        uint64  scheduledStart;        // lesson start time (Unix timestamp)
        uint32  durationMinutes;       // planned duration of the lesson
        LessonStatus status;           // lifecycle status (see enum above)
        bool studentApproved;          // manual override flag by the student
        bool resolved;                 // true once funds have been paid or refunded
    }

    /// @notice Platform wallet that receives the platformFee
    address payable public platformWallet;

    /// @notice Trusted oracle address that can call resolveLesson()
    address public oracle;

    /// @notice Mapping of all lessons by their unique identifier
    mapping(bytes32 => Lesson) public lessons;

    /// @notice Emitted when a new lesson is created
    event LessonCreated(
        bytes32 indexed lessonId,
        address indexed student,
        address indexed teacher,
        uint256 lessonPrice,
        uint256 platformFee
    );

    /// @notice Emitted when a lesson is funded by the student
    event LessonFunded(bytes32 indexed lessonId, uint256 totalAmount);

    /// @notice Emitted when a lesson is resolved (paid or refunded)
    event LessonResolved(
        bytes32 indexed lessonId,
        LessonStatus status,
        uint8 teacherPct,
        uint8 studentPct
    );

    /// @notice Emitted when a lesson is cancelled before funding
    event LessonCancelled(bytes32 indexed lessonId);

    /// @notice Emitted when the oracle address is updated
    event OracleChanged(address indexed oldOracle, address indexed newOracle);

    /// @notice Emitted when the platform wallet is updated
    event PlatformWalletChanged(address indexed oldWallet, address indexed newWallet);

    /// @dev Restricts a function so that only the oracle can call it
    modifier onlyOracle() {
        require(msg.sender == oracle, "Only oracle");
        _;
    }

    /// @dev Restricts a function so that only the platform wallet can call it
    modifier onlyPlatform() {
        require(msg.sender == platformWallet, "Only platform");
        _;
    }

    /// @param _platformWallet Address that receives the platform fees
    /// @param _oracle Address of the trusted oracle server wallet
    constructor(address payable _platformWallet, address _oracle) {
        require(_platformWallet != address(0), "Invalid platform wallet");
        require(_oracle != address(0), "Invalid oracle");
        platformWallet = _platformWallet;
        oracle = _oracle;
    }

    // -------------------------------------------------------------------------
    // Admin functions (platform only)
    // -------------------------------------------------------------------------

    /// @notice Update the oracle address (e.g. if the server wallet changes)
    function setOracle(address _oracle) external onlyPlatform {
        require(_oracle != address(0), "Invalid oracle");
        emit OracleChanged(oracle, _oracle);
        oracle = _oracle;
    }

    /// @notice Update the platform wallet address
    function setPlatformWallet(address payable _platformWallet) external onlyPlatform {
        require(_platformWallet != address(0), "Invalid wallet");
        emit PlatformWalletChanged(platformWallet, _platformWallet);
        platformWallet = _platformWallet;
    }

    // -------------------------------------------------------------------------
    // Core lesson lifecycle functions
    // -------------------------------------------------------------------------

    /// @notice Create a new lesson (no funds are moved yet)
    /// @param lessonId Unique identifier of the lesson (e.g. keccak256 hash)
    /// @param teacher Wallet address of the teacher
    /// @param lessonPrice Amount to be paid to the teacher (in MATIC)
    /// @param platformFee Amount to be paid to the platform (in MATIC)
    /// @param scheduledStart Planned start time (Unix timestamp)
    /// @param durationMinutes Planned lesson duration in minutes
    function createLesson(
        bytes32 lessonId,
        address payable teacher,
        uint256 lessonPrice,
        uint256 platformFee,
        uint64 scheduledStart,
        uint32 durationMinutes
    ) external {
        require(lessons[lessonId].teacher == address(0), "Lesson already exists");
        require(teacher != address(0), "Invalid teacher");
        require(lessonPrice > 0, "Price must be > 0");

        lessons[lessonId] = Lesson({
            student: payable(msg.sender),
            teacher: teacher,
            lessonPrice: lessonPrice,
            platformFee: platformFee,
            scheduledStart: scheduledStart,
            durationMinutes: durationMinutes,
            status: LessonStatus.Created,
            studentApproved: false,
            resolved: false
        });

        emit LessonCreated(lessonId, msg.sender, teacher, lessonPrice, platformFee);
    }

    /// @notice Fund a lesson by sending lessonPrice + platformFee in MATIC
    /// @dev Only the student who created the lesson can fund it
    function fundLesson(bytes32 lessonId) external payable {
        Lesson storage lesson = lessons[lessonId];

        require(lesson.student == msg.sender, "Only student can fund");
        require(lesson.status == LessonStatus.Created, "Lesson not in Created status");

        uint256 total = lesson.lessonPrice + lesson.platformFee;
        require(msg.value == total, "Incorrect value sent");

        lesson.status = LessonStatus.Funded;

        emit LessonFunded(lessonId, total);
    }

    /// @notice Student can manually approve payment (override) at any time after funding
    /// @dev This implements the "manual override" scenario
    function approvePayment(bytes32 lessonId) external {
        Lesson storage lesson = lessons[lessonId];

        require(lesson.student == msg.sender, "Only student can approve");
        require(lesson.status == LessonStatus.Funded, "Lesson not funded");
        require(!lesson.resolved, "Lesson already resolved");

        // Mark lesson as resolved BEFORE sending funds (checks-effects-interactions)
        lesson.studentApproved = true;
        lesson.resolved = true;
        lesson.status = LessonStatus.ResolvedPaid;

        uint256 teacherAmount = lesson.lessonPrice;
        uint256 feeAmount = lesson.platformFee;

        // Pay teacher
        (bool ok1, ) = lesson.teacher.call{value: teacherAmount}("");
        require(ok1, "Teacher payment failed");

        // Pay platform fee
        (bool ok2, ) = platformWallet.call{value: feeAmount}("");
        require(ok2, "Platform payment failed");

        // For manual override we treat it as 100% / 100%
        emit LessonResolved(lessonId, lesson.status, 100, 100);
    }

    /// @notice Oracle resolves the lesson based on attendance percentages
    /// @param lessonId Identifier of the lesson
    /// @param teacherPct Attendance percentage of the teacher (0-100)
    /// @param studentPct Attendance percentage of the student (0-100)
    function resolveLesson(
        bytes32 lessonId,
        uint8 teacherPct,
        uint8 studentPct
    ) external onlyOracle {
        Lesson storage lesson = lessons[lessonId];

        require(lesson.status == LessonStatus.Funded, "Lesson not funded");
        require(!lesson.resolved, "Lesson already resolved");

        // Mark as resolved so it cannot be processed twice
        lesson.resolved = true;

        // If the student already approved, always pay the teacher
        if (lesson.studentApproved) {
            lesson.status = LessonStatus.ResolvedPaid;
            _payOut(lesson, lessonId, teacherPct, studentPct);
            return;
        }

        bool payTeacher;

        // 1) Happy path: both attended >= 95%
        if (teacherPct >= 95 && studentPct >= 95) {
            payTeacher = true;
        }
        // 2) Student no-show: teacher >= 95%, student < 5%
        else if (teacherPct >= 95 && studentPct < 5) {
            payTeacher = true;
        }
        // 3) Teacher no-show: teacher < 5%, student >= 95%
        else if (teacherPct < 5 && studentPct >= 95) {
            payTeacher = false;
        }
        // 4) All other edge cases: default to refund in the MVP
        else {
            payTeacher = false;
        }

        if (payTeacher) {
            lesson.status = LessonStatus.ResolvedPaid;
            _payOut(lesson, lessonId, teacherPct, studentPct);
        } else {
            lesson.status = LessonStatus.ResolvedRefunded;
            _refund(lesson, lessonId, teacherPct, studentPct);
        }
    }

    /// @notice Student can cancel a lesson before funding
    function cancelLesson(bytes32 lessonId) external {
        Lesson storage lesson = lessons[lessonId];

        require(lesson.student == msg.sender, "Only student can cancel");
        require(lesson.status == LessonStatus.Created, "Can only cancel before funding");

        lesson.status = LessonStatus.Cancelled;
        lesson.resolved = true;

        emit LessonCancelled(lessonId);
    }

    // -------------------------------------------------------------------------
    // Internal helpers: payout and refund
    // -------------------------------------------------------------------------

    /// @dev Internal helper to pay teacher and platform
    function _payOut(
        Lesson storage lesson,
        bytes32 lessonId,
        uint8 teacherPct,
        uint8 studentPct
    ) internal {
        uint256 teacherAmount = lesson.lessonPrice;
        uint256 feeAmount = lesson.platformFee;

        (bool ok1, ) = lesson.teacher.call{value: teacherAmount}("");
        require(ok1, "Teacher payment failed");

        (bool ok2, ) = platformWallet.call{value: feeAmount}("");
        require(ok2, "Platform payment failed");

        emit LessonResolved(lessonId, lesson.status, teacherPct, studentPct);
    }

    /// @dev Internal helper to refund the student (lessonPrice + platformFee)
    function _refund(
        Lesson storage lesson,
        bytes32 lessonId,
        uint8 teacherPct,
        uint8 studentPct
    ) internal {
        uint256 total = lesson.lessonPrice + lesson.platformFee;

        (bool ok, ) = lesson.student.call{value: total}("");
        require(ok, "Refund failed");

        emit LessonResolved(lessonId, lesson.status, teacherPct, studentPct);
    }
}
