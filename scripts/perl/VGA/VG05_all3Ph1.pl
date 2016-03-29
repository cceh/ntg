#! /usr/bin/perl -w
# VG05_all3.pl -- MySQL:Textwert:ivv7srv16.uni-muenster.de
# VG05_all kapitelweise fŸllen auf der Basis von Vergleichen einzelner Variantenspektren in `ECM_Acts_Sp`

# 1. VG_05 erweitern um die fŸr das aktuelle Kapitel benštigten Felder

#ALTER TABLE `VG05_all` ADD `GTXT1` INT(3) NOT NULL;
#ALTER TABLE `VG05_all` DROP `GTXT1`

# 2. Vergleich mit den AuszŸgen aus att durchfŸhren
# 3. Summieren

use strict;
use DBI;
use access;

#@ _VARDECL_
my $DEBUG = 0;
#my $dsn = "DBI:mysql:Textwert:ivv7srv16.uni-muenster.de";	# data source name
my $dsn = "DBI:mysql:ECM_Acts_Mss:localhost";	# data source name

my $user_name = getUsername();						# user name
my $password = getPassword();						# password

my $dbh = DBI->connect ($dsn, $user_name, $password,
						{ RaiseError => 1, PrintError => 0, mysql_enable_utf8 => 1 });

###AKTUELL ZU BEARBEITENDES KAPITEL###
my $chn = $ARGV[0];

#hšchste Nummer der bereits bearbeiteten Kapitel
#wird bei Summierungsupdate benštigt
my $maxchn = 28; # DO NOT CHANGE!

my $chnstr;
my $chnstr2;
if ($chn < 10)
{
	$chnstr = 'Apg0'.$chn;
	$chnstr2 = '0'.$chn;
} else {
	$chnstr = 'Apg'.$chn;
	$chnstr2 = $chn;
}

my $source1 = '`ECM_Acts_Mss`.`ActsMsList`';
my $target = '`ECM_Acts_VG`.`VG05_all`';

my ($sth, @ary, $ary, $gtxt, $ueges, $lac, $hsnr, @msl, $ms, @cpmsl, $cpms);

#Felder fŸr die Werte zu diesem Kapitel vorbereiten
my $fgtxt = 'GTXT'.$chn;
my $fueges = 'UEGES'.$chn;
my $fuegesq = 'UEGESQ'.$chn;

$dbh->do ("UPDATE $target SET `$fgtxt` = 0, `$fueges` = 0, `$fuegesq` = 0; ");

###Gibt es die nštigen Felder schon?
my $c = $dbh->do ("SHOW COLUMNS FROM $target WHERE FIELD = '$fgtxt'");
if ($c != 1)
{
	$dbh->do ("ALTER TABLE $target ADD `$fgtxt` INT(3) NOT NULL; ");
	$dbh->do ("ALTER TABLE $target ADD `$fueges` INT(3) NOT NULL; ");
	$dbh->do ("ALTER TABLE $target ADD `$fuegesq` DECIMAL(4,1) NOT NULL; ");
}

$dbh->do ("UPDATE $target SET `$fgtxt` = 0, `$fueges` = 0, `$fuegesq` = 0; ");

$sth = $dbh->prepare ("SELECT MS FROM $source1 WHERE `$chnstr` = 1");
$sth->execute();
	
while (@ary = $sth->fetchrow_array())
{
	@msl = (@msl, @ary);
}

foreach $ms(@msl)
{
	my $source2 = '`ECM_Acts_Sp_'.$chnstr2.'`.`Acts'.$chnstr2.'_'.$ms.'`';
	if ($DEBUG) { print "source2: ".$source2."\n"; }
	$sth = $dbh->prepare ("SELECT VGMS FROM $target WHERE `MS` = $ms");
	$sth->execute();
	
	while (@ary = $sth->fetchrow_array())
	{
		my $testcpms = $dbh->selectrow_array ("SELECT `MS` FROM $source1 WHERE `MS` = $ary[0] AND `$chnstr` = 1");
		if (defined $testcpms)
		{
			@cpmsl = (@cpmsl, @ary);
			undef $testcpms;
		} 
	}
	
	foreach $cpms(@cpmsl)
	{
		my $source3 = '`ECM_Acts_Sp_'.$chnstr2.'`.`Acts'.$chnstr2.'_'.$cpms.'`';
		if ($DEBUG) { print "source3: ".$source3."\n"; }
		$gtxt = 0;
		$ueges = 0;
		
		$sth = $dbh->prepare ("SELECT ANFADR, ENDADR, LABEZ FROM $source2");
		$sth->execute();
	
		while (@ary = $sth->fetchrow_array())
		{
			if ($ary[2] eq 'zz' or $ary[2] eq 'zv' or $ary[2] eq 'zu' or $ary[2] eq 'zw')
			{
				next;
			} else {
				my $sql  = "SELECT LABEZ FROM $source3 WHERE ANFADR = $ary[0] AND ENDADR = $ary[1]; ";
				if ($DEBUG) { print "$sql\n"; }
				my $cplabez = $dbh->selectrow_array ($sql);
				
#		print "$source3\n$cplabez\n";
	
				if ($cplabez eq 'zz' or $cplabez eq 'zv' or $cplabez eq 'zu' or $cplabez eq 'zw')
				{
					next;
				} else {
					$gtxt = $gtxt+1;
					
					if ($ary[2] eq $cplabez)
					{
						$ueges = $ueges+1;
					}
				}
			}	
		}
		
		my $cmd = "UPDATE $target SET `$fgtxt` = $gtxt, `$fueges` = $ueges, `$fuegesq` = $ueges*100/$gtxt WHERE `MS`=$ms AND `VGMS`=$cpms";
		if ($DEBUG) { print $cmd."\n"; } 
		$dbh->do ($cmd);
		
	}
	
	undef @cpmsl;
}

################
###Summierung###
################

#Bereits eingegebene Werte lšschen
$dbh->do ("UPDATE $target SET `GTXT` = 0");
$dbh->do ("UPDATE $target SET `UEGES` = 0");
$dbh->do ("UPDATE $target SET `UEGESQ` = 0");

my $n = 0;
while ($n < $maxchn)
{
	$n++;
	$gtxt = '`GTXT'.$n.'`';
	$ueges = '`UEGES'.$n.'`';
	
	$dbh->do ("UPDATE $target SET `GTXT` = `GTXT`+$gtxt, `UEGES` = `UEGES`+$ueges");
	
	$dbh->do ("UPDATE $target SET `UEGESQ` = `UEGES`*100/`GTXT`");
}

$sth->finish ();

$dbh->disconnect ();

exit (0);
