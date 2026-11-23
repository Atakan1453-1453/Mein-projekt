<?php

declare(strict_types=1);

namespace Koenigshof\Kontakt\Tests;

use Koenigshof\Kontakt\RateLimiter;
use PHPUnit\Framework\TestCase;

final class RateLimiterTest extends TestCase
{
    private string $dir;

    protected function setUp(): void
    {
        $this->dir = sys_get_temp_dir() . '/kontakt-rl-' . bin2hex(random_bytes(4));
    }

    protected function tearDown(): void
    {
        foreach (glob($this->dir . '/{,.}*', GLOB_BRACE) ?: [] as $f) {
            if (is_file($f)) {
                unlink($f);
            }
        }
        @rmdir($this->dir);
    }

    public function testBlocksAfterLimitAndResetsAfterWindow(): void
    {
        $rl = new RateLimiter($this->dir, str_repeat('s', 40), 3, 3600);
        $t = 1_800_000_000;
        self::assertTrue($rl->hit('203.0.113.5', $t));
        self::assertTrue($rl->hit('203.0.113.5', $t + 1));
        self::assertTrue($rl->hit('203.0.113.5', $t + 2));
        self::assertFalse($rl->hit('203.0.113.5', $t + 3), 'Vierter Versuch muss blockiert werden');
        self::assertTrue($rl->hit('198.51.100.7', $t + 3), 'Andere IP ist nicht betroffen');
        self::assertTrue($rl->hit('203.0.113.5', $t + 3601), 'Nach Ablauf des Fensters wieder erlaubt');
    }

    public function testIpIsNotStoredInPlainText(): void
    {
        $rl = new RateLimiter($this->dir, str_repeat('s', 40), 3, 3600);
        $rl->hit('203.0.113.5', 1_800_000_000);
        foreach (glob($this->dir . '/*') ?: [] as $file) {
            self::assertStringNotContainsString('203.0.113.5', basename($file));
            self::assertStringNotContainsString('203.0.113.5', (string) file_get_contents($file));
        }
        self::assertFileExists($this->dir . '/.htaccess');
    }

    public function testSweepDeletesOldEntries(): void
    {
        $rl = new RateLimiter($this->dir, str_repeat('s', 40), 3, 3600);
        $rl->hit('203.0.113.5', 1_800_000_000);
        $files = glob($this->dir . '/*.json') ?: [];
        self::assertCount(1, $files);
        touch($files[0], time() - 7200);
        $rl->sweep(time());
        self::assertCount(0, glob($this->dir . '/*.json') ?: []);
    }
}
