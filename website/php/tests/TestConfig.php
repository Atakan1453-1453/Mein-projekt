<?php

declare(strict_types=1);

namespace Koenigshof\Kontakt\Tests;

use Koenigshof\Kontakt\Config;

/** Erzeugt eine Test-Konfiguration auf Basis der echten form-config. */
final class TestConfig
{
    /** @param array<string, mixed> $overrides */
    public static function create(array $overrides = [], ?string $storage = null): Config
    {
        $form = json_decode((string) file_get_contents(__DIR__ . '/../../src/config/contact-form.json'), true);
        $storage ??= sys_get_temp_dir() . '/kontakt-test-' . bin2hex(random_bytes(4));

        return Config::fromArrays(array_replace_recursive([
            'recipient' => 'empfang@example.de',
            'from' => 'website@example.de',
            'transport' => 'file',
            'secret' => str_repeat('a1b2c3d4', 8),
            'allowed_origins' => ['https://galeriekoenigshof.de'],
            'storage_dir' => $storage,
            'site_name' => 'Galerie Königshof',
        ], $overrides), $form);
    }

    /** @return array<string, string> gültige Formulardaten */
    public static function validInput(): array
    {
        return [
            'anliegen' => 'vermietung',
            'name' => 'Erika Mustermann',
            'firma' => 'Muster Mode GmbH',
            'email' => 'erika@example.org',
            'telefon' => '+49 (2104) 123-456',
            'branche' => 'Damenmode',
            'flaeche' => '120',
            'zeitraum' => 'ab Frühjahr 2027',
            'nachricht' => "Guten Tag,\nwir interessieren uns für eine Fläche in Ihrem Center.",
            'website' => '',
        ];
    }
}
