import java.util.*;
import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.io.*;

// Displays the welcome banner and today's date.
class Welcome {
    void showWelcome() {
        System.out.println(" _____                     _    ______                               \n" +
                            "|_   _|                   | |   |  ___|                              \n" +
                            "  | |   _ __   __ _   ___ | | __| |_     ___   _ __   ___   ___  ___ \n" +
                            "  | |  | '__| / _` | / __|| |/ /|  _|   / _ \\ | '__| / __| / _ \\/ __|\n" +
                            "  | |  | |   | (_| || (__ |   < | |    | (_) || |   | (__ |  __/\\__ \\\n" +
                            "  \\_/  |_|    \\__,_| \\___||_|\\_\\\\_|     \\___/ |_|    \\___| \\___||___/");

        LocalDate today = LocalDate.now();
        DateTimeFormatter formatter = DateTimeFormatter.ofPattern("dd MMMM yyyy");
        String formattedToday = today.format(formatter);

        System.out.println();
        System.out.println("+--------------------------------------------+");
        System.out.printf("| %-42s |\n", "Today's Date: " + formattedToday);
        System.out.println("+--------------------------------------------+");
    }
}

// Handles logging the questions solved today into a file.
class InputData {
    void logTodayQuestions() {
        Scanner scanner = new Scanner(System.in);

        System.out.println("Great! How many questions did you do today?\n");
        int qns = scanner.nextInt();

        System.out.println("What was the rating for each question?");
        int sum = 0;
        StringBuilder ratingLog = new StringBuilder();
        int rated800 = 0, rated900 = 0, rated1000 = 0, rated1100 = 0, rated1200 = 0, rated1300 = 0;

        for (int i = 0; i < qns; i++) {
            int temp = scanner.nextInt();
            switch (temp) {
                case 800:
                    rated800++;
                    break;
                case 900:
                    rated900++;
                    break;
                case 1000:
                    rated1000++;
                    break;
                case 1100:
                    rated1100++;
                    break;
                case 1200:
                    rated1200++;
                    break;
                case 1300:
                    rated1300++;
                    break;
            }
            sum += temp;
            ratingLog.append(temp).append(" ");
        }

        int avg = sum / qns;

        // Print summary
        System.out.println();
        System.out.println("You've solved " + qns + " questions, totaling " + sum + " rating points with an average of "
                + avg + ".");

        try {
            // Write to log file
            BufferedWriter logWriter = new BufferedWriter(new FileWriter("trackforces_log.txt", true));
            LocalDate today = LocalDate.now();
            DateTimeFormatter formatter = DateTimeFormatter.ofPattern("dd MMMM yyyy");
            String formattedDate = today.format(formatter);

            logWriter.write("Date: " + formattedDate + "\n");
            logWriter.write("Solved: " + qns + "\n");
            logWriter.write("Ratings: " + ratingLog.toString().trim() + "\n");
            logWriter.write("Average: " + avg + "\n");
            logWriter.write("------------------------------\n");
            logWriter.close();

            // Read previous stats
            int temp800 = 0, temp900 = 0, temp1000 = 0, temp1100 = 0, temp1200 = 0, temp1300 = 0;
            try {
                BufferedReader statsReader = new BufferedReader(new FileReader("trackforces_stats.txt"));
                temp800 = Integer.parseInt(statsReader.readLine());
                temp900 = Integer.parseInt(statsReader.readLine());
                temp1000 = Integer.parseInt(statsReader.readLine());
                temp1100 = Integer.parseInt(statsReader.readLine());
                temp1200 = Integer.parseInt(statsReader.readLine());
                temp1300 = Integer.parseInt(statsReader.readLine());
                statsReader.close();
            } catch (Exception e) {
                // First-time run or file missing — use defaults (0)
            }

            // Update and write new stats
            temp800 += rated800;
            temp900 += rated900;
            temp1000 += rated1000;
            temp1100 += rated1100;
            temp1200 += rated1200;
            temp1300 += rated1300;

            BufferedWriter statsWriter = new BufferedWriter(new FileWriter("trackforces_stats.txt"));
            statsWriter.write(temp800 + "\n");
            statsWriter.write(temp900 + "\n");
            statsWriter.write(temp1000 + "\n");
            statsWriter.write(temp1100 + "\n");
            statsWriter.write(temp1200 + "\n");
            statsWriter.write(temp1300 + "\n");
            statsWriter.close();

            System.out.println("✅ Your session has been saved to trackforces_log.txt.");
        } catch (IOException e) {
            System.out.println("❌ Error writing to file: " + e.getMessage());
        }
    }
}

// Handles reading and displaying logs and stats.
class OutputData {
    void viewLog() {
        System.out.println("\n=== 📓 TrackForces Log ===\n");

        try {
            BufferedReader reader = new BufferedReader(new FileReader("trackforces_log.txt"));
            String line;
            while ((line = reader.readLine()) != null) {
                System.out.println(line);
            }
            reader.close();
        } catch (FileNotFoundException e) {
            System.out.println("❌ Log file not found. Try adding a session first.");
        } catch (IOException e) {
            System.out.println("❌ Error reading the log file.");
        }
    }

    void viewStats() {
        System.out.println("\n=== 📊 TrackForces Stats ===\n");

        try {
            BufferedReader reader = new BufferedReader(new FileReader("trackforces_stats.txt"));
            int rated800 = Integer.parseInt(reader.readLine());
            int rated900 = Integer.parseInt(reader.readLine());
            int rated1000 = Integer.parseInt(reader.readLine());
            int rated1100 = Integer.parseInt(reader.readLine());
            int rated1200 = Integer.parseInt(reader.readLine());
            int rated1300 = Integer.parseInt(reader.readLine());
            reader.close();

            int total = rated800 + rated900 + rated1000 + rated1100 + rated1200 + rated1300;

            System.out.println("800 rated solved  : " + rated800);
            System.out.println("900 rated solved  : " + rated900);
            System.out.println("1000 rated solved : " + rated1000);
            System.out.println("1100 rated solved : " + rated1100);
            System.out.println("1200 rated solved : " + rated1200);
            System.out.println("1300 rated solved : " + rated1300);
            System.out.println("-----------------------");
            System.out.println("Total solved      : " + total);
        } catch (FileNotFoundException e) {
            System.out.println("❌ Stats file not found.");
        } catch (IOException | NumberFormatException e) {
            System.out.println("❌ Error reading stats file.");
        }
    }
}

// Main class that shows the menu and handles user input.
public class TrackForces {
    public static void main(String[] args) {
        Scanner scanner = new Scanner(System.in);
        Welcome welcome = new Welcome();
        InputData input = new InputData();
        OutputData output = new OutputData();

        welcome.showWelcome();

        while (true) {
            System.out.println("\nChoose an option:\n");
            System.out.println("1. Log today's questions");
            System.out.println("2. Display previous logs");
            System.out.println("3. View stats");
            System.out.println("4. Exit TrackForces");
            System.out.print("> ");

            int choice = scanner.nextInt();

            switch (choice) {
                case 1:
                    input.logTodayQuestions();
                    System.out.println("Press Enter to go back");
                    scanner.nextLine();
                    scanner.nextLine();
                    break;

                case 2:
                    output.viewLog();
                    System.out.println("Press Enter to go back");
                    scanner.nextLine();
                    scanner.nextLine();
                    break;

                case 3:
                    output.viewStats();
                    System.out.println("Press Enter to go back");
                    scanner.nextLine();
                    scanner.nextLine();
                    break;

                case 4:
                    System.out.println("👋 Exiting... Keep grinding!");
                    return;

                default:
                    System.out.println("Invalid option, try again.");
                    break;
            }
        }
    }
}
