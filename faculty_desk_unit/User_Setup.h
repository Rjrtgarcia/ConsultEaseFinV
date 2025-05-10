// User setup file for the TFT_eSPI library for the ConsultEase Faculty Desk Unit
// For ESP32 with 2.4" TFT SPI Display (ST7789)

// => Copy this file to the libraries/TFT_eSPI folder in your Arduino IDE

#define USER_SETUP_INFO "ConsultEase Faculty Desk Unit"

// Define the ESP32 board
#define ESP32_PARALLEL

// Comment out the next line to use SPI interface instead of parallel
//#define TFT_PARALLEL_8_BIT

// Display driver
#define ST7789_DRIVER

// Display resolution
#define TFT_WIDTH  240
#define TFT_HEIGHT 320

// For ST7789 display in Landscape orientation
#define CGRAM_OFFSET

// Color depth
#define SPI_FREQUENCY  27000000   // Works with SPI display
//#define SPI_FREQUENCY  40000000 // Maximum for ST7789 but might be unstable

// ESP32 Pin configuration for SPI display
// VSPI port is used (/CS=GPIO5, MOSI=GPIO23, MISO=GPIO19, SCK=GPIO18)
#define TFT_MISO 19
#define TFT_MOSI 23
#define TFT_SCLK 18
#define TFT_CS   5   // Chip select control pin
#define TFT_DC   2   // Data Command control pin
#define TFT_RST  4   // Reset pin
#define TFT_BL   15  // LED back-light

// Touch screen chip select - set to -1 if touch is not used
#define TOUCH_CS -1

// Comment out to use SPI read for TFT
#define TFT_SPI_MODE SPI_MODE0

// Load the font files
#define LOAD_GLCD   // Font 1. Original Adafruit 8 pixel font needs ~1820 bytes in FLASH
#define LOAD_FONT2  // Font 2. Small 16 pixel high font, needs ~3534 bytes in FLASH, 96 characters
#define LOAD_FONT4  // Font 4. Medium 26 pixel high font, needs ~5848 bytes in FLASH, 96 characters
#define LOAD_FONT6  // Font 6. Large 48 pixel font, needs ~2666 bytes in FLASH, only characters 1234567890:-.apm
#define LOAD_FONT7  // Font 7. 7 segment 48 pixel font, needs ~2438 bytes in FLASH, only characters 1234567890:.
#define LOAD_FONT8  // Font 8. Large 75 pixel font needs ~3256 bytes in FLASH, only characters 1234567890:-.
//#define LOAD_FONT8N // Font 8 narrow, only characters 1234567890:-.

// Additional options
#define SMOOTH_FONT
//#define SPI_TOUCH  // Saves DMA channel if SPI display is used

// Swap bytes in 16-bit color transfers
// #define TFT_RGB_ORDER TFT_RGB  // Colour order Red-Green-Blue
#define TFT_RGB_ORDER TFT_BGR  // Colour order Blue-Green-Red

// Avoid conflict with SUPPORT_TRANSACTIONS in the library
//#define SUPPORT_TRANSACTIONS 